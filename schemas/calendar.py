from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    all_day: Optional[bool] = False
    color: Optional[str] = None
    location: Optional[str] = None
    reminder: Optional[bool] = False


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    color: Optional[str] = None
    location: Optional[str] = None
    reminder: Optional[bool] = None


class EventResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    all_day: bool
    color: Optional[str]
    location: Optional[str]
    reminder: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventList(BaseModel):
    events: List[EventResponse]
    total: int