from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models.todo import TodoPriority, TodoStatus


class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: TodoPriority = TodoPriority.MEDIUM
    due_date: Optional[datetime] = None


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None
    is_archived: Optional[bool] = None


class TodoResponse(TodoBase):
    id: str
    status: TodoStatus
    user_id: str
    completed_at: Optional[datetime]
    is_archived: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TodoList(BaseModel):
    todos: list[TodoResponse]
    total: int
    page: int
    limit: int


class TodoStats(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int
    cancelled: int