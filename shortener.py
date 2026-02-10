import redis
import secrets
import string
from config import Config

r = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    decode_responses=True
)

def generate_short_code(length=6) -> str:
    characters = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(secrets.choice(characters) for _ in range(length))
        if not r.exists(f"url:{short_code}"):
            return short_code