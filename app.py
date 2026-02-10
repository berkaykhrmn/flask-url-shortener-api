import json
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, jwt_required
from auth_schemas import RegisterIn, LoginIn, AuthOut
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import redirect, render_template, request
from apiflask import APIFlask, abort
from config import Config
from schemas import ShortenIn, ShortenOut
from shortener import generate_short_code, r
from models import User
from datetime import datetime
from worker import fetch_url_preview


app = APIFlask(__name__, title="URL Shortener API", version="1.0.0", docs_path="/docs")
app.config.from_object(Config)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=Config.RATELIMIT_STORAGE_URL,
    default_limits=["200 per day", "50 per hour"],
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window",
    enabled=not app.config.get("TESTING", False)
)

jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES

@app.post("/auth/register")
@app.input(RegisterIn)
@app.output(AuthOut, status_code=201)
@app.doc(
    summary="Register a new user",
    description="Create a new user account with email and password",
    tags=["Authentication"]
)
@limiter.limit("5 per hour")
def register(json_data):
    email = json_data["email"]
    password = json_data["password"]

    user = User.create(email, password)

    if not user:
        abort(409, "Email already registered")

    access_token = create_access_token(identity=str(user.user_id))

    return {
        "access_token": access_token,
        "user_id": str(user.user_id),
        "email": user.email,
    }, 201


@app.post("/auth/login")
@app.input(LoginIn)
@app.output(AuthOut)
@app.doc(
    summary="Login user",
    description="Authenticate user and get JWT token",
    tags=["Authentication"]
)
@limiter.limit("10 per hour")
def login(json_data):
    email = json_data["email"]
    password = json_data["password"]

    user = User.get_by_email(email)

    if not user or not user.verify_password(password):
        abort(401, "Invalid email or password")

    access_token = create_access_token(identity=str(user.user_id))

    return {
        "access_token": access_token,
        "user_id": str(user.user_id),
        "email": user.email
    }


@app.get("/auth/me")
@app.doc(
    summary="Get current user",
    description="Get current authenticated user info",
    tags=["Authentication"]
)
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.get_by_id(int(user_id))

    if not user:
        abort(404, "User not found")

    return {
        "user_id": str(user.user_id),
        "email": user.email
    }

@app.get("/my-links")
@app.doc(
    summary="Get user's shortened links",
    description="Returns all shortened URLs created by the authenticated user",
    tags=["User Links"]
)
@jwt_required()
@limiter.limit("30 per minute")
def get_my_links():
    user_id = get_jwt_identity()

    links_codes = r.smembers(f"user:{user_id}:links")

    if not links_codes:
        return {"links": [], "total": 0}
    links = []

    for short_code in links_codes:
        metadata_raw = r.get(f"metadata:{short_code}")
        if not metadata_raw:
            continue

        metadata = json.loads(metadata_raw)

        clicks_key = f"clicks:{short_code}"
        total_clicks = r.get(clicks_key) or 0

        ip_keys = r.keys(f"clicks:{short_code}:ip:*")
        unique_ips = len(ip_keys) if ip_keys else 0

        ttl = r.ttl(f"url:{short_code}")

        links.append({
            "short_code": short_code,
            "short_url": f"{Config.BASE_URL}/{short_code}",
            "original_url": metadata.get("original_url"),
            "created_at": metadata.get("created_at"),
            "total_clicks": int(total_clicks),
            "unique_ips": unique_ips,
            "expires_in_seconds": ttl if ttl > 0 else 0
        })

        links.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return {
            "links": links,
            "total": len(links),
        }

@app.route("/")
@limiter.exempt
def root():
    return render_template("index.html")


@app.post("/shorten")
@app.input(ShortenIn)
@app.output(ShortenOut)
@app.doc(
    summary="Shorten a URL",
    description="Creates a shortened URL. Supports custom codes and tracks existing URLs.",
    tags=["URL Shortener"],
)
@limiter.limit("10 per minute")
@jwt_required(optional=True)
def shorten(json_data):
    long_url = json_data["url"]
    custom = json_data.get("custom_code")
    user_id = get_jwt_identity()

    if not long_url.startswith(('http://', 'https://')):
        long_url = 'https://' + long_url

    expiry_time = 604800 if user_id else 86400

    if custom:
        short_code = custom
        key = f"url:{short_code}"

        if r.exists(key):
            existing_url = r.get(key)
            clicks_key = f"clicks:{short_code}"
            total_clicks = int(r.get(clicks_key) or 0)
            ip_keys = r.keys(f"clicks:{short_code}:ip:*")
            unique_ips = len(ip_keys)

            return {
                "short_url": f"{Config.BASE_URL}/{short_code}",
                "original_url": existing_url,
                "custom_used": True,
                "already_existed": True,
                "total_clicks": total_clicks,
                "unique_ips": unique_ips,
                "expires_in_seconds": int(r.ttl(key)),
                "message": "This custom code is already in use."
            }, 200

        if not (4 <= len(custom) <= 16 and custom.isalnum()):
            abort(400, "Invalid custom code")

    existing_short_code = r.get(f"long_to_short:{long_url}")

    if existing_short_code and not custom:
        short_code = existing_short_code
        already_existed = True
        status_code = 200
        current_expiry = int(r.ttl(f"url:{short_code}"))
    else:
        if not custom:
            short_code = generate_short_code()

        r.setex(f"url:{short_code}", expiry_time, long_url)
        r.setex(f"long_to_short:{long_url}", expiry_time, short_code)

        if user_id:
            metadata = {
                "user_id": str(user_id),
                "created_at": datetime.now().isoformat(),
                "original_url": long_url,
            }
            r.setex(f"metadata:{short_code}", expiry_time, json.dumps(metadata))
            r.sadd(f"user:{user_id}:links", short_code)

        already_existed = False
        status_code = 201
        current_expiry = expiry_time
        if status_code == 201:
            fetch_url_preview.delay(short_code, long_url)

    return {
        "short_url": f"{Config.BASE_URL}/{short_code}",
        "original_url": long_url,
        "custom_used": bool(custom),
        "already_existed": already_existed,
        "expires_in_seconds": current_expiry,
        "user_id": user_id,
    }, status_code

@app.get("/<short_code>")
@app.doc(
    summary="Redirect to original URL",
    description="Redirects to the original URL and increments click statistics.",
    tags=["URL Shortener"],
    responses={404: "URL not found"},
)
@limiter.limit("100 per minute")
def redirect_short(short_code):
    key = f"url:{short_code}"
    long_url = r.get(key)

    if not long_url:
        abort(404, "URL not found")

    clicks_key = f"clicks:{short_code}"
    r.incr(clicks_key)

    ip = request.remote_addr
    ip_key = f"clicks:{short_code}:ip:{ip}"
    r.incr(ip_key)

    return redirect(long_url, code=302)

@app.get("/preview/<short_code>")
def get_preview(short_code):
    data = r.get(f"preview:{short_code}")
    if data:
        return json.loads(data)
    return {"message": "Preview pending or not available"}, 404

@app.get("/stats/<short_code>")
@app.doc(
    summary="Get URL statistics",
    description="Returns total clicks and unique visitor count for a shortened URL.",
    tags=["Statistics"]
)
@limiter.limit("30 per minute")
def get_stats(short_code):
    clicks_key = f"clicks:{short_code}"
    total_clicks = r.get(clicks_key) or b"0"
    total_clicks = int(total_clicks)

    ip_keys = r.keys(f"clicks:{short_code}:ip:*")
    unique_ips = len(ip_keys) if ip_keys else 0

    return {
        "short_code": short_code,
        "total_clicks": total_clicks,
        "unique_ips": unique_ips
    }

@app.errorhandler(429)
def ratelimit_handler(e):
    return {
        "error": "Rate limit exceeded",
        "message": str(e.description),
    }, 429

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

