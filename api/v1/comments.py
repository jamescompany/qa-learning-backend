from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from database import get_db
from schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentList
)
from dependencies import (
    get_current_user,
    PaginationParams
)
from models import User, Comment, Post
from core.exceptions import (
    CommentNotFoundException,
    PostNotFoundException,
    InsufficientPermissionsException,
    BadRequestException
)

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.get("/post/{post_id}", response_model=CommentList)
async def get_post_comments(
    post_id: str,
    pagination: PaginationParams = Depends(),
    include_replies: bool = Query(True, description="Include nested replies"),
    db: Session = Depends(get_db)
):
    """Get comments for a specific post"""
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise PostNotFoundException()
    
    # Get top-level comments
    query = db.query(Comment).options(
        joinedload(Comment.author)
    ).filter(
        and_(
            Comment.post_id == post_id,
            Comment.parent_id == None,
            Comment.is_deleted == False
        )
    )
    
    # Apply sorting
    if pagination.order == "asc":
        query = query.order_by(Comment.created_at.asc())
    else:
        query = query.order_by(Comment.created_at.desc())
    
    total = query.count()
    comments = query.offset(pagination.offset).limit(pagination.limit).all()
    
    # Load replies if requested
    if include_replies:
        for comment in comments:
            comment.replies = db.query(Comment).options(
                joinedload(Comment.author)
            ).filter(
                and_(
                    Comment.parent_id == comment.id,
                    Comment.is_deleted == False
                )
            ).order_by(Comment.created_at.asc()).all()
    
    return {
        "comments": comments,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: str,
    db: Session = Depends(get_db)
):
    """Get comment by ID"""
    comment = db.query(Comment).options(
        joinedload(Comment.author)
    ).filter(
        and_(
            Comment.id == comment_id,
            Comment.is_deleted == False
        )
    ).first()
    
    if not comment:
        raise CommentNotFoundException()
    
    # Load replies
    comment.replies = db.query(Comment).options(
        joinedload(Comment.author)
    ).filter(
        and_(
            Comment.parent_id == comment.id,
            Comment.is_deleted == False
        )
    ).order_by(Comment.created_at.asc()).all()
    
    return comment


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_create: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new comment"""
    # Check if post exists
    post = db.query(Post).filter(Post.id == comment_create.post_id).first()
    if not post:
        raise PostNotFoundException()
    
    # Check if parent comment exists (for replies)
    if comment_create.parent_id:
        parent = db.query(Comment).filter(
            and_(
                Comment.id == comment_create.parent_id,
                Comment.post_id == comment_create.post_id,
                Comment.is_deleted == False
            )
        ).first()
        
        if not parent:
            raise CommentNotFoundException(detail="Parent comment not found")
        
        # Prevent deeply nested comments (max 2 levels)
        if parent.parent_id is not None:
            raise BadRequestException(detail="Cannot reply to a reply")
    
    comment = Comment(
        content=comment_create.content,
        post_id=comment_create.post_id,
        author_id=current_user.id,
        parent_id=comment_create.parent_id
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Load author info
    comment.author = current_user
    comment.replies = []
    
    return comment


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update comment by ID"""
    comment = db.query(Comment).options(
        joinedload(Comment.author)
    ).filter(
        and_(
            Comment.id == comment_id,
            Comment.is_deleted == False
        )
    ).first()
    
    if not comment:
        raise CommentNotFoundException()
    
    # Check permissions
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise InsufficientPermissionsException()
    
    # Update comment
    comment.content = comment_update.content
    comment.is_edited = True
    
    db.commit()
    db.refresh(comment)
    
    # Load replies
    comment.replies = db.query(Comment).options(
        joinedload(Comment.author)
    ).filter(
        and_(
            Comment.parent_id == comment.id,
            Comment.is_deleted == False
        )
    ).order_by(Comment.created_at.asc()).all()
    
    return comment


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete comment by ID (soft delete)"""
    comment = db.query(Comment).filter(
        and_(
            Comment.id == comment_id,
            Comment.is_deleted == False
        )
    ).first()
    
    if not comment:
        raise CommentNotFoundException()
    
    # Check permissions
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise InsufficientPermissionsException()
    
    # Soft delete
    comment.is_deleted = True
    comment.content = "[Deleted]"
    
    db.commit()
    
    return {"message": "Comment deleted successfully"}


@router.get("/user/{user_id}", response_model=CommentList)
async def get_user_comments(
    user_id: str,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db)
):
    """Get all comments by a specific user"""
    query = db.query(Comment).options(
        joinedload(Comment.author),
        joinedload(Comment.post)
    ).filter(
        and_(
            Comment.author_id == user_id,
            Comment.is_deleted == False
        )
    )
    
    # Apply sorting
    if pagination.order == "asc":
        query = query.order_by(Comment.created_at.asc())
    else:
        query = query.order_by(Comment.created_at.desc())
    
    total = query.count()
    comments = query.offset(pagination.offset).limit(pagination.limit).all()
    
    return {
        "comments": comments,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


@router.get("/my-comments", response_model=CommentList)
async def get_my_comments(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's comments"""
    query = db.query(Comment).options(
        joinedload(Comment.author),
        joinedload(Comment.post)
    ).filter(
        and_(
            Comment.author_id == current_user.id,
            Comment.is_deleted == False
        )
    )
    
    # Apply sorting
    if pagination.order == "asc":
        query = query.order_by(Comment.created_at.asc())
    else:
        query = query.order_by(Comment.created_at.desc())
    
    total = query.count()
    comments = query.offset(pagination.offset).limit(pagination.limit).all()
    
    return {
        "comments": comments,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }