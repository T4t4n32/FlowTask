"""
Modelos de datos para eventos.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class RecurrencePattern(BaseModel):
    frequency: str  # daily, weekly, monthly
    interval: int = 1
    by_day: list[str] | None = None
    until: datetime | None = None


class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    user_id: str
    summary: str
    description: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    location: str | None = None
    status: EventStatus = EventStatus.CONFIRMED
    recurrence: RecurrencePattern | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
