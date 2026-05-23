from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any

class UserActivityEvent(BaseModel):
    user_id: int
    event_type: str = Field(..., max_length=50)
    timestamp: datetime
    metadata: Dict[str, Any]