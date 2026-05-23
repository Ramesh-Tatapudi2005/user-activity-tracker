import pytest
from src.models import UserActivity

def test_user_activity_model_creation():
    activity = UserActivity(
        user_id=123,
        event_type="login",
        timestamp="2023-10-27T10:00:00",
        metadata_payload={"session": "abc"}
    )
    assert activity.user_id == 123
    assert activity.event_type == "login"
    assert activity.metadata_payload["session"] == "abc"