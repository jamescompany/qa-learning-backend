from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models.post import PostStatus
from .user import UserPublic


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=200)


class TagCreate(TagBase):
    pass


class TagResponse(TagBase):
    id: str
    slug: str
    created_at: datetime

    class Config:
        from_attributes = True


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    featured_image: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    is_featured: bool = False


class PostCreate(PostBase):
    tags: Optional[List[str]] = []  # Tag IDs


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    excerpt: Optional[str] = Field(None, max_length=500)
    featured_image: Optional[str] = None
    status: Optional[PostStatus] = None
    is_featured: Optional[bool] = None
    tags: Optional[List[str]] = None  # Tag IDs


class PostResponse(PostBase):
    id: str
    slug: str
    author_id: str
    author: UserPublic
    view_count: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    tags: List[TagResponse]
    comment_count: Optional[int] = 0

    class Config:
        from_attributes = True


class PostList(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    limit: int


class PostPublic(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    featured_image: Optional[str]
    author: UserPublic
    view_count: int
    published_at: Optional[datetime]
    tags: List[TagResponse]

    class Config:
        from_attributes = True