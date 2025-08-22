from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class PostLike(Base):
    __tablename__ = "post_likes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure a user can only like a post once
    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='unique_post_user_like'),
    )
    
    # Relationships
    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="liked_posts")
    
    def __repr__(self):
        return f"<PostLike(post_id={self.post_id}, user_id={self.user_id})>"