import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import User, Post, Todo, Comment, Tag, PostTag, UserRole, PostStatus, TodoStatus, TodoPriority
from core import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_users(db: Session):
    """Create sample users"""
    users_data = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "full_name": "Admin User",
            "role": UserRole.ADMIN,
            "is_verified": True,
            "bio": "System administrator"
        },
        {
            "email": "john@example.com",
            "username": "johndoe",
            "full_name": "John Doe",
            "role": UserRole.USER,
            "is_verified": True,
            "bio": "Software developer and tech enthusiast"
        },
        {
            "email": "jane@example.com",
            "username": "janesmith",
            "full_name": "Jane Smith",
            "role": UserRole.USER,
            "is_verified": True,
            "bio": "Full-stack developer"
        },
        {
            "email": "moderator@example.com",
            "username": "moderator",
            "full_name": "Moderator User",
            "role": UserRole.MODERATOR,
            "is_verified": True,
            "bio": "Content moderator"
        },
        {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "role": UserRole.USER,
            "is_verified": False,
            "bio": "Test account"
        }
    ]
    
    users = []
    for user_data in users_data:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(
                **user_data,
                hashed_password=get_password_hash("password123"),
                is_active=True
            )
            db.add(user)
            users.append(user)
            logger.info(f"Created user: {user.username}")
        else:
            users.append(existing)
            logger.info(f"User already exists: {existing.username}")
    
    db.commit()
    return users


def seed_tags(db: Session):
    """Create sample tags"""
    tags_data = [
        {"name": "Python", "slug": "python", "description": "Python programming language"},
        {"name": "JavaScript", "slug": "javascript", "description": "JavaScript programming language"},
        {"name": "React", "slug": "react", "description": "React framework"},
        {"name": "FastAPI", "slug": "fastapi", "description": "FastAPI framework"},
        {"name": "Database", "slug": "database", "description": "Database related topics"},
        {"name": "Tutorial", "slug": "tutorial", "description": "Tutorial posts"},
        {"name": "Tips", "slug": "tips", "description": "Tips and tricks"},
        {"name": "News", "slug": "news", "description": "Tech news"},
    ]
    
    tags = []
    for tag_data in tags_data:
        existing = db.query(Tag).filter(Tag.slug == tag_data["slug"]).first()
        if not existing:
            tag = Tag(**tag_data)
            db.add(tag)
            tags.append(tag)
            logger.info(f"Created tag: {tag.name}")
        else:
            tags.append(existing)
            logger.info(f"Tag already exists: {existing.name}")
    
    db.commit()
    return tags


def seed_posts(db: Session, users: list[User], tags: list[Tag]):
    """Create sample posts"""
    posts_data = [
        {
            "title": "Getting Started with FastAPI",
            "slug": "getting-started-with-fastapi",
            "content": "FastAPI is a modern, fast web framework for building APIs with Python...",
            "excerpt": "Learn the basics of FastAPI",
            "status": PostStatus.PUBLISHED,
            "is_featured": True,
            "view_count": 150
        },
        {
            "title": "React Hooks Explained",
            "slug": "react-hooks-explained",
            "content": "React Hooks revolutionized how we write React components...",
            "excerpt": "Understanding React Hooks",
            "status": PostStatus.PUBLISHED,
            "is_featured": True,
            "view_count": 200
        },
        {
            "title": "Database Design Best Practices",
            "slug": "database-design-best-practices",
            "content": "Good database design is crucial for application performance...",
            "excerpt": "Essential database design tips",
            "status": PostStatus.PUBLISHED,
            "view_count": 100
        },
        {
            "title": "Python Tips and Tricks",
            "slug": "python-tips-and-tricks",
            "content": "Here are some useful Python tips that can improve your code...",
            "excerpt": "Useful Python tips",
            "status": PostStatus.PUBLISHED,
            "view_count": 175
        },
        {
            "title": "Draft Post Example",
            "slug": "draft-post-example",
            "content": "This is a draft post that is not yet published...",
            "excerpt": "Draft post",
            "status": PostStatus.DRAFT,
            "view_count": 0
        }
    ]
    
    posts = []
    for i, post_data in enumerate(posts_data):
        existing = db.query(Post).filter(Post.slug == post_data["slug"]).first()
        if not existing:
            post = Post(
                **post_data,
                author_id=users[i % len(users)].id,
                published_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                if post_data["status"] == PostStatus.PUBLISHED else None
            )
            db.add(post)
            db.flush()
            
            # Add random tags
            num_tags = random.randint(1, 3)
            for tag in random.sample(tags, num_tags):
                post_tag = PostTag(post_id=post.id, tag_id=tag.id)
                db.add(post_tag)
            
            posts.append(post)
            logger.info(f"Created post: {post.title}")
        else:
            posts.append(existing)
            logger.info(f"Post already exists: {existing.title}")
    
    db.commit()
    return posts


def seed_todos(db: Session, users: list[User]):
    """Create sample todos"""
    todos_data = [
        {
            "title": "Complete project documentation",
            "description": "Write comprehensive documentation for the API",
            "status": TodoStatus.IN_PROGRESS,
            "priority": TodoPriority.HIGH
        },
        {
            "title": "Review pull requests",
            "description": "Review and merge pending PRs",
            "status": TodoStatus.TODO,
            "priority": TodoPriority.MEDIUM
        },
        {
            "title": "Fix bug in authentication",
            "description": "Users reporting login issues",
            "status": TodoStatus.TODO,
            "priority": TodoPriority.URGENT
        },
        {
            "title": "Update dependencies",
            "description": "Update all npm and pip packages",
            "status": TodoStatus.DONE,
            "priority": TodoPriority.LOW,
            "completed_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "title": "Write unit tests",
            "description": "Add tests for new features",
            "status": TodoStatus.TODO,
            "priority": TodoPriority.HIGH
        }
    ]
    
    todos = []
    for user in users[:3]:  # Create todos for first 3 users
        for todo_data in todos_data:
            todo = Todo(
                **todo_data,
                user_id=user.id,
                due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14))
                if todo_data["status"] != TodoStatus.DONE else None
            )
            db.add(todo)
            todos.append(todo)
            logger.info(f"Created todo for {user.username}: {todo.title}")
    
    db.commit()
    return todos


def seed_comments(db: Session, posts: list[Post], users: list[User]):
    """Create sample comments"""
    comments_data = [
        "Great article! Very helpful.",
        "Thanks for sharing this information.",
        "I have a question about this topic...",
        "This helped me solve my problem!",
        "Can you provide more examples?",
        "Excellent explanation!",
        "I disagree with some points here.",
        "Looking forward to more content like this."
    ]
    
    comments = []
    for post in posts[:3]:  # Add comments to first 3 posts
        num_comments = random.randint(2, 5)
        for i in range(num_comments):
            comment = Comment(
                content=random.choice(comments_data),
                post_id=post.id,
                author_id=random.choice(users).id
            )
            db.add(comment)
            comments.append(comment)
    
    db.commit()
    logger.info(f"Created {len(comments)} comments")
    return comments


def seed_database():
    """Seed the database with sample data"""
    logger.info("Starting database seeding...")
    
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Seed data
        users = seed_users(db)
        tags = seed_tags(db)
        posts = seed_posts(db, users, tags)
        todos = seed_todos(db, users)
        comments = seed_comments(db, posts, users)
        
        logger.info("Database seeding completed successfully!")
        
        # Print summary
        print("\n" + "="*50)
        print("DATABASE SEEDED SUCCESSFULLY!")
        print("="*50)
        print(f"Users created: {len(users)}")
        print(f"Tags created: {len(tags)}")
        print(f"Posts created: {len(posts)}")
        print(f"Todos created: {len(todos)}")
        print(f"Comments created: {len(comments)}")
        print("\nDefault password for all users: password123")
        print("Admin email: admin@example.com")
        print("="*50 + "\n")
        
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()