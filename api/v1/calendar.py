from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database import get_db
from schemas.calendar import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventList
)
from dependencies import get_current_user
from models import User, CalendarEvent
from core.exceptions import EventNotFoundException, InsufficientPermissionsException

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("/events", response_model=EventList)
async def get_events(
    start_date: Optional[date] = Query(None, description="Start date for event range"),
    end_date: Optional[date] = Query(None, description="End date for event range"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's calendar events"""
    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id)
    
    if start_date:
        query = query.filter(CalendarEvent.start_time >= start_date)
    
    if end_date:
        query = query.filter(CalendarEvent.end_time <= end_date)
    
    events = query.order_by(CalendarEvent.start_time).all()
    
    return EventList(
        events=[EventResponse.from_orm(event) for event in events],
        total=len(events)
    )


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific calendar event"""
    event = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    ).first()
    
    if not event:
        raise EventNotFoundException(f"Event with id {event_id} not found")
    
    return EventResponse.from_orm(event)


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new calendar event"""
    event = CalendarEvent(
        user_id=current_user.id,
        **event_data.dict()
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return EventResponse.from_orm(event)


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a calendar event"""
    event = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    ).first()
    
    if not event:
        raise EventNotFoundException(f"Event with id {event_id} not found")
    
    for field, value in event_data.dict(exclude_unset=True).items():
        setattr(event, field, value)
    
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    
    return EventResponse.from_orm(event)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a calendar event"""
    event = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    ).first()
    
    if not event:
        raise EventNotFoundException(f"Event with id {event_id} not found")
    
    db.delete(event)
    db.commit()
    
    return {"message": "Event deleted successfully"}