from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from database import Base


class PostStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String, nullable=True)
    featured_image = Column(String, nullable=True)
    status = Column(SQLEnum(PostStatus), default=PostStatus.DRAFT, nullable=False)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    likes_count = Column(Integer, default=0, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Post(id={self.id}, title={self.title}, status={self.status})>"


class Tag(Base):
    __tablename__ = "tags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    posts = relationship("Post", secondary="post_tags", back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"


class PostTag(Base):
    __tablename__ = "post_tags"

    post_id = Column(String, ForeignKey("posts.id"), primary_key=True)
    tag_id = Column(String, ForeignKey("tags.id"), primary_key=True)