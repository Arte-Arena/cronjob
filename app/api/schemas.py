# app/api/schemas.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class MessageScheduleRequest(BaseModel):
    clients: List[str]
    template: str
    send_at: datetime