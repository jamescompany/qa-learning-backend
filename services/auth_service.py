from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from core import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_verification_code,
    validate_password
)
from core.exceptions import (
    InvalidCredentialsException,
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
    UserNotFoundException,
    InvalidTokenException,
    BadRequestException
)
from models import User
from schemas.auth import RegisterRequest, LoginRequest
import secrets
import logging

logger = logging.getLogger(__name__)


class AuthService:
    @staticmethod
    def register(db: Session, request: RegisterRequest) -> User:
        # Check if email exists
        if db.query(User).filter(User.email == request.email).first():
            raise EmailAlreadyExistsException()
        
        # Check if username exists
        if db.query(User).filter(User.username == request.username).first():
            raise UsernameAlreadyExistsException()
        
        # Validate password strength
        is_valid, message = validate_password(request.password)
        if not is_valid:
            raise BadRequestException(detail=message)
        
        # Create new user
        verification_code = generate_verification_code()
        hashed_password = get_password_hash(request.password)
        
        user = User(
            email=request.email,
            username=request.username,
            hashed_password=hashed_password,
            full_name=request.full_name,
            verification_code=verification_code,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"New user registered: {user.email}")
        return user
    
    @staticmethod
    def login(db: Session, request: LoginRequest) -> dict:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise InvalidCredentialsException()
        
        # Verify password
        if not verify_password(request.password, user.hashed_password):
            raise InvalidCredentialsException()
        
        # Check if user is active
        if not user.is_active:
            raise BadRequestException(detail="User account is inactive")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        logger.info(f"User logged in: {user.email}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def refresh_token(db: Session, refresh_token: str) -> dict:
        try:
            user_id = verify_token(refresh_token, "refresh")
        except Exception:
            raise InvalidTokenException()
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()
        
        if not user.is_active:
            raise BadRequestException(detail="User account is inactive")
        
        # Create new access token
        access_token = create_access_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def verify_email(db: Session, user: User, code: str) -> User:
        if user.is_verified:
            raise BadRequestException(detail="Email already verified")
        
        if user.verification_code != code:
            raise BadRequestException(detail="Invalid verification code")
        
        user.is_verified = True
        user.verification_code = None
        db.commit()
        db.refresh(user)
        
        logger.info(f"Email verified for user: {user.email}")
        return user
    
    @staticmethod
    def request_password_reset(db: Session, email: str) -> str:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Return success even if user not found (security)
            return "Password reset instructions sent if account exists"
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.reset_password_token = reset_token
        user.reset_password_expire = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        logger.info(f"Password reset requested for: {user.email}")
        return reset_token
    
    @staticmethod
    def reset_password(db: Session, token: str, new_password: str) -> User:
        user = db.query(User).filter(User.reset_password_token == token).first()
        
        if not user:
            raise InvalidTokenException(detail="Invalid or expired reset token")
        
        if user.reset_password_expire < datetime.utcnow():
            raise InvalidTokenException(detail="Reset token has expired")
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            raise BadRequestException(detail=message)
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        user.reset_password_token = None
        user.reset_password_expire = None
        db.commit()
        db.refresh(user)
        
        logger.info(f"Password reset for user: {user.email}")
        return user
    
    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str) -> User:
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestException(detail="Current password is incorrect")
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            raise BadRequestException(detail=message)
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        
        logger.info(f"Password changed for user: {user.email}")
        return user