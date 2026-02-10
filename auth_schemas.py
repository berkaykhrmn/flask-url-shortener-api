from apiflask import Schema
from apiflask.fields import String, Email
from apiflask.validators import Length


class RegisterIn(Schema):
    email = Email(required=True, metadata={"description": "User email address"})
    password = String(
        required=True,
        validate=Length(min=8, max=128),
        metadata={"description": "Password (min 8 characters)"}
    )


class LoginIn(Schema):
    email = Email(required=True, metadata={"description": "User email address"})
    password = String(required=True, metadata={"description": "User password"})


class AuthOut(Schema):
    access_token = String(metadata={"description": "JWT access token"})
    user_id = String(metadata={"description": "User ID"})
    email = String(metadata={"description": "User email"})