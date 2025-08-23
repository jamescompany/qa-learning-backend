from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class CardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = "medium"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = []
    position: Optional[int] = 0


class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    position: Optional[int] = None
    column_id: Optional[str] = None


class CardResponse(BaseModel):
    id: str
    column_id: str
    title: str
    description: Optional[str]
    assignee: Optional[str]
    priority: str
    due_date: Optional[datetime]
    tags: List[str]
    position: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ColumnCreate(BaseModel):
    title: str
    position: Optional[int] = 0


class ColumnUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[int] = None


class ColumnResponse(BaseModel):
    id: str
    board_id: str
    title: str
    position: int
    cards: List[CardResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BoardCreate(BaseModel):
    title: str
    description: Optional[str] = None


class BoardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class BoardResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    columns: List[ColumnResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BoardList(BaseModel):
    boards: List[BoardResponse]
    total: int


class CardMoveRequest(BaseModel):
    target_column_id: str
    position: Optional[int] = None