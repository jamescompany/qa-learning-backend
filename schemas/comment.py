from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .user import UserPublic


class CommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class CommentCreate(CommentBase):
    post_id: str
    parent_id: Optional[str] = None


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class CommentResponse(CommentBase):
    id: str
    post_id: str
    author_id: str
    author: UserPublic
    parent_id: Optional[str]
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    replies: Optional[List["CommentResponse"]] = []

    class Config:
        from_attributes = True


CommentResponse.model_rebuild()


class CommentList(BaseModel):
    comments: List[CommentResponse]
    total: int
    page: int
    limit: int