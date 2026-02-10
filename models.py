import redis
import json
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from config import Config

r = redis.Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    db=Config.REDIS_DB,
    decode_responses=True
)

ph = PasswordHasher()


class User:
    def __init__(self, user_id, email, password_hash=None):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def create(email, password):
        if r.exists(f"user:email:{email}"):
            return None

        user_id = r.incr("user:id:counter")
        password_hash = ph.hash(password)

        user_data = {
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash
        }

        r.set(f"user:id:{user_id}", json.dumps(user_data))
        r.set(f"user:email:{email}", user_id)

        return User(user_id, email, password_hash)

    @staticmethod
    def get_by_email(email):
        user_id = r.get(f"user:email:{email}")
        if not user_id:
            return None

        return User.get_by_id(int(user_id))

    @staticmethod
    def get_by_id(user_id):
        user_data = r.get(f"user:id:{user_id}")
        if not user_data:
            return None

        data = json.loads(user_data)
        return User(
            user_id=data["user_id"],
            email=data["email"],
            password_hash=data["password_hash"]
        )

    def verify_password(self, password):
        try:
            ph.verify(self.password_hash, password)

            if ph.check_needs_rehash(self.password_hash):
                self.password_hash = ph.hash(password)
                self._update_password_hash()

            return True
        except VerifyMismatchError:
            return False

    def _update_password_hash(self):
        user_data = r.get(f"user:id:{self.user_id}")
        if user_data:
            data = json.loads(user_data)
            data["password_hash"] = self.password_hash
            r.set(f"user:id:{self.user_id}", json.dumps(data))