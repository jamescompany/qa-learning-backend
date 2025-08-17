from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_
from core.exceptions import (
    PostNotFoundException,
    BadRequestException,
    InsufficientPermissionsException
)
from models import Post, PostStatus, Tag, PostTag, User
from schemas.post import PostCreate, PostUpdate
import re
import logging

logger = logging.getLogger(__name__)


class PostService:
    @staticmethod
    def create_slug(title: str) -> str:
        """Generate URL-friendly slug from title"""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    @staticmethod
    def get_post(db: Session, post_id: str) -> Post:
        post = db.query(Post).options(
            joinedload(Post.author),
            joinedload(Post.tags),
            joinedload(Post.comments)
        ).filter(Post.id == post_id).first()
        
        if not post:
            raise PostNotFoundException()
        return post
    
    @staticmethod
    def get_post_by_slug(db: Session, slug: str) -> Post:
        post = db.query(Post).options(
            joinedload(Post.author),
            joinedload(Post.tags),
            joinedload(Post.comments)
        ).filter(Post.slug == slug).first()
        
        if not post:
            raise PostNotFoundException()
        return post
    
    @staticmethod
    def get_posts(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        status: Optional[PostStatus] = None,
        author_id: Optional[str] = None,
        tag_id: Optional[str] = None,
        search: Optional[str] = None,
        is_featured: Optional[bool] = None,
        sort_by: str = "created_at",
        order: str = "desc"
    ) -> List[Post]:
        query = db.query(Post).options(
            joinedload(Post.author),
            joinedload(Post.tags)
        )
        
        # Apply filters
        if status:
            query = query.filter(Post.status == status)
        
        if author_id:
            query = query.filter(Post.author_id == author_id)
        
        if tag_id:
            query = query.join(PostTag).filter(PostTag.tag_id == tag_id)
        
        if is_featured is not None:
            query = query.filter(Post.is_featured == is_featured)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Post.title.ilike(search_filter),
                    Post.content.ilike(search_filter),
                    Post.excerpt.ilike(search_filter)
                )
            )
        
        # Apply sorting
        if sort_by == "view_count":
            order_column = Post.view_count
        elif sort_by == "published_at":
            order_column = Post.published_at
        else:
            order_column = Post.created_at
        
        if order == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def count_posts(
        db: Session,
        status: Optional[PostStatus] = None,
        author_id: Optional[str] = None,
        tag_id: Optional[str] = None,
        search: Optional[str] = None,
        is_featured: Optional[bool] = None
    ) -> int:
        query = db.query(Post)
        
        if status:
            query = query.filter(Post.status == status)
        
        if author_id:
            query = query.filter(Post.author_id == author_id)
        
        if tag_id:
            query = query.join(PostTag).filter(PostTag.tag_id == tag_id)
        
        if is_featured is not None:
            query = query.filter(Post.is_featured == is_featured)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Post.title.ilike(search_filter),
                    Post.content.ilike(search_filter),
                    Post.excerpt.ilike(search_filter)
                )
            )
        
        return query.count()
    
    @staticmethod
    def create_post(db: Session, post_create: PostCreate, author_id: str) -> Post:
        # Generate unique slug
        base_slug = PostService.create_slug(post_create.title)
        slug = base_slug
        counter = 1
        
        while db.query(Post).filter(Post.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create post
        post = Post(
            title=post_create.title,
            slug=slug,
            content=post_create.content,
            excerpt=post_create.excerpt,
            featured_image=post_create.featured_image,
            status=post_create.status,
            is_featured=post_create.is_featured,
            author_id=author_id
        )
        
        # Set published date if publishing
        if post_create.status == PostStatus.PUBLISHED:
            post.published_at = datetime.utcnow()
        
        db.add(post)
        db.flush()  # Get post ID before adding tags
        
        # Add tags
        if post_create.tags:
            for tag_id in post_create.tags:
                tag = db.query(Tag).filter(Tag.id == tag_id).first()
                if tag:
                    post_tag = PostTag(post_id=post.id, tag_id=tag_id)
                    db.add(post_tag)
        
        db.commit()
        db.refresh(post)
        
        logger.info(f"Post created: {post.title} by {author_id}")
        return post
    
    @staticmethod
    def update_post(
        db: Session,
        post_id: str,
        post_update: PostUpdate,
        user: User
    ) -> Post:
        post = PostService.get_post(db, post_id)
        
        # Check permissions
        if post.author_id != user.id and user.role != "admin":
            raise InsufficientPermissionsException()
        
        update_data = post_update.dict(exclude_unset=True)
        
        # Update slug if title changed
        if "title" in update_data:
            base_slug = PostService.create_slug(update_data["title"])
            if base_slug != post.slug:
                slug = base_slug
                counter = 1
                while db.query(Post).filter(
                    and_(Post.slug == slug, Post.id != post_id)
                ).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                update_data["slug"] = slug
        
        # Update published date if status changes to published
        if "status" in update_data:
            if update_data["status"] == PostStatus.PUBLISHED and not post.published_at:
                update_data["published_at"] = datetime.utcnow()
        
        # Update tags if provided
        if "tags" in update_data:
            # Remove old tags
            db.query(PostTag).filter(PostTag.post_id == post_id).delete()
            
            # Add new tags
            for tag_id in update_data["tags"]:
                tag = db.query(Tag).filter(Tag.id == tag_id).first()
                if tag:
                    post_tag = PostTag(post_id=post_id, tag_id=tag_id)
                    db.add(post_tag)
            
            del update_data["tags"]
        
        # Update post fields
        for field, value in update_data.items():
            setattr(post, field, value)
        
        db.commit()
        db.refresh(post)
        
        logger.info(f"Post updated: {post.title}")
        return post
    
    @staticmethod
    def delete_post(db: Session, post_id: str, user: User) -> bool:
        post = PostService.get_post(db, post_id)
        
        # Check permissions
        if post.author_id != user.id and user.role != "admin":
            raise InsufficientPermissionsException()
        
        db.delete(post)
        db.commit()
        
        logger.info(f"Post deleted: {post.title}")
        return True
    
    @staticmethod
    def increment_view_count(db: Session, post_id: str) -> Post:
        post = PostService.get_post(db, post_id)
        post.view_count += 1
        db.commit()
        db.refresh(post)
        return post
    
    @staticmethod
    def get_or_create_tag(db: Session, tag_name: str) -> Tag:
        tag_slug = PostService.create_slug(tag_name)
        tag = db.query(Tag).filter(Tag.slug == tag_slug).first()
        
        if not tag:
            tag = Tag(
                name=tag_name,
                slug=tag_slug
            )
            db.add(tag)
            db.commit()
            db.refresh(tag)
        
        return tag