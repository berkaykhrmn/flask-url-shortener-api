from apiflask import Schema
from apiflask.fields import String, Boolean, Integer

class ShortenIn(Schema):
    url = String(required=True)
    custom_code = String(
        required=False,
        metadata={"description": "Custom short code (4-16 alphanumeric characters)", "example": "mylink"}
    )

class ShortenOut(Schema):
        short_url = String(metadata={"description": "The shortened URL"})
        original_url = String(metadata={"description": "The original long URL"})
        custom_used = Boolean(metadata={"description": "Whether a custom code was used"})
        already_existed = Boolean(metadata={"description": "Whether this URL was already shortened"})
        expires_in_seconds = Integer(metadata={"description": "Expiration time in seconds"})
        total_clicks = Integer(required=False, metadata={"description": "Total click count"})
        unique_ips = Integer(required=False, metadata={"description": "Unique visitor count"})
        message = String(required=False, metadata={"description": "Info message"})
        user_id = String(required=False, metadata={"description": "Owner user ID"})
        created_at = String(required=False, metadata={"description": "Creation timestamp"})
