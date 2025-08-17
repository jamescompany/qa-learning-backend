from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.exceptions import (
    UserNotFoundException,
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    BadRequestException
)
from models import User, UserRole
from schemas.user import UserCreate, UserUpdate
from core import get_password_hash, validate_password
import logging

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def get_user(db: Session, user_id: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> List[User]:
        query = db.query(User)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_filter),
                    User.username.ilike(search_filter),
                    User.full_name.ilike(search_filter)
                )
            )
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def count_users(
        db: Session,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> int:
        query = db.query(User)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_filter),
                    User.username.ilike(search_filter),
                    User.full_name.ilike(search_filter)
                )
            )
        
        if role:
            query = query.filter(User.role == role)
        
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)
        
        return query.count()
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        # Check if email exists
        if UserService.get_user_by_email(db, user_create.email):
            raise EmailAlreadyExistsException()
        
        # Check if username exists
        if UserService.get_user_by_username(db, user_create.username):
            raise UsernameAlreadyExistsException()
        
        # Validate password
        is_valid, message = validate_password(user_create.password)
        if not is_valid:
            raise BadRequestException(detail=message)
        
        # Create user
        hashed_password = get_password_hash(user_create.password)
        user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            bio=user_create.bio,
            avatar_url=user_create.avatar_url
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created: {user.email}")
        return user
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_update: UserUpdate) -> User:
        user = UserService.get_user(db, user_id)
        
        update_data = user_update.dict(exclude_unset=True)
        
        # Check email uniqueness if updating
        if "email" in update_data and update_data["email"] != user.email:
            if UserService.get_user_by_email(db, update_data["email"]):
                raise EmailAlreadyExistsException()
        
        # Check username uniqueness if updating
        if "username" in update_data and update_data["username"] != user.username:
            if UserService.get_user_by_username(db, update_data["username"]):
                raise UsernameAlreadyExistsException()
        
        # Update user fields
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user.email}")
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        user = UserService.get_user(db, user_id)
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted: {user.email}")
        return True
    
    @staticmethod
    def activate_user(db: Session, user_id: str) -> User:
        user = UserService.get_user(db, user_id)
        user.is_active = True
        db.commit()
        db.refresh(user)
        
        logger.info(f"User activated: {user.email}")
        return user
    
    @staticmethod
    def deactivate_user(db: Session, user_id: str) -> User:
        user = UserService.get_user(db, user_id)
        user.is_active = False
        db.commit()
        db.refresh(user)
        
        logger.info(f"User deactivated: {user.email}")
        return user
    
    @staticmethod
    def update_user_role(db: Session, user_id: str, role: UserRole) -> User:
        user = UserService.get_user(db, user_id)
        user.role = role
        db.commit()
        db.refresh(user)
        
        logger.info(f"User role updated: {user.email} -> {role}")
        return user