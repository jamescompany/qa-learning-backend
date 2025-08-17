from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from database import get_db
from schemas.post import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostList,
    TagResponse,
    TagCreate
)
from services.post_service import PostService
from dependencies import (
    get_current_user,
    get_current_verified_user,
    PaginationParams
)
from models import User, PostStatus, Tag

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=PostList)
async def get_posts(
    pagination: PaginationParams = Depends(),
    status: Optional[PostStatus] = Query(None, description="Filter by status"),
    author_id: Optional[str] = Query(None, description="Filter by author ID"),
    tag_id: Optional[str] = Query(None, description="Filter by tag ID"),
    search: Optional[str] = Query(None, description="Search in title, content, excerpt"),
    is_featured: Optional[bool] = Query(None, description="Filter featured posts"),
    db: Session = Depends(get_db)
):
    """Get list of posts with filters"""
    # Public users can only see published posts
    if not status:
        status = PostStatus.PUBLISHED
    
    posts = PostService.get_posts(
        db,
        skip=pagination.offset,
        limit=pagination.limit,
        status=status,
        author_id=author_id,
        tag_id=tag_id,
        search=search,
        is_featured=is_featured,
        sort_by=pagination.sort_by or "created_at",
        order=pagination.order
    )
    
    total = PostService.count_posts(
        db,
        status=status,
        author_id=author_id,
        tag_id=tag_id,
        search=search,
        is_featured=is_featured
    )
    
    # Add comment count to each post
    for post in posts:
        post.comment_count = len(post.comments) if hasattr(post, 'comments') else 0
    
    return {
        "posts": posts,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


@router.get("/my-posts", response_model=PostList)
async def get_my_posts(
    pagination: PaginationParams = Depends(),
    status: Optional[PostStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in title, content, excerpt"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's posts"""
    posts = PostService.get_posts(
        db,
        skip=pagination.offset,
        limit=pagination.limit,
        status=status,
        author_id=current_user.id,
        search=search,
        sort_by=pagination.sort_by or "created_at",
        order=pagination.order
    )
    
    total = PostService.count_posts(
        db,
        status=status,
        author_id=current_user.id,
        search=search
    )
    
    for post in posts:
        post.comment_count = len(post.comments) if hasattr(post, 'comments') else 0
    
    return {
        "posts": posts,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    increment_view: bool = Query(True, description="Increment view count"),
    db: Session = Depends(get_db)
):
    """Get post by ID"""
    post = PostService.get_post(db, post_id)
    
    # Only increment view for published posts
    if increment_view and post.status == PostStatus.PUBLISHED:
        PostService.increment_view_count(db, post_id)
    
    post.comment_count = len(post.comments) if hasattr(post, 'comments') else 0
    return post


@router.get("/slug/{slug}", response_model=PostResponse)
async def get_post_by_slug(
    slug: str,
    increment_view: bool = Query(True, description="Increment view count"),
    db: Session = Depends(get_db)
):
    """Get post by slug"""
    post = PostService.get_post_by_slug(db, slug)
    
    # Only increment view for published posts
    if increment_view and post.status == PostStatus.PUBLISHED:
        PostService.increment_view_count(db, post.id)
    
    post.comment_count = len(post.comments) if hasattr(post, 'comments') else 0
    return post


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_create: PostCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a new post"""
    post = PostService.create_post(db, post_create, current_user.id)
    post.comment_count = 0
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_update: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update post by ID"""
    post = PostService.update_post(db, post_id, post_update, current_user)
    post.comment_count = len(post.comments) if hasattr(post, 'comments') else 0
    return post


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete post by ID"""
    PostService.delete_post(db, post_id, current_user)
    return {"message": "Post deleted successfully"}


# Tag endpoints

@router.get("/tags/all", response_model=list[TagResponse])
async def get_all_tags(
    db: Session = Depends(get_db)
):
    """Get all tags"""
    tags = db.query(Tag).all()
    return tags


@router.post("/tags/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_create: TagCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a new tag"""
    tag = PostService.get_or_create_tag(db, tag_create.name)
    if tag_create.description:
        tag.description = tag_create.description
        db.commit()
        db.refresh(tag)
    return tag