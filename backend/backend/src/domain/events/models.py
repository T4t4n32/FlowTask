"""
Modelos de datos para eventos.
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class EventStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class RecurrencePattern(BaseModel):
    frequency: str  # daily, weekly, monthly
    interval: int = 1
    by_day: Optional[List[str]] = None
    until: Optional[datetime] = None


class CalendarEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"evt_{datetime.now().timestamp()}")
    user_id: str
    summary: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    status: EventStatus = EventStatus.CONFIRMED
    recurrence: Optional[RecurrencePattern] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
