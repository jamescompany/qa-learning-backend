from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database import get_db
from schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
    VerifyEmailRequest
)
from schemas.user import UserResponse
from services import AuthService
from dependencies import get_current_user, limiter
from models import User
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    user = AuthService.register(db, register_data)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login with email and password"""
    return AuthService.login(db, login_data)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    return current_user


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    # Update allowed fields only
    allowed_fields = ["full_name", "bio", "avatar_url"]
    for field in allowed_fields:
        if field in update_data:
            setattr(current_user, field, update_data[field])
    
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    return AuthService.refresh_token(db, request.refresh_token)


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify email with verification code"""
    user = AuthService.verify_email(db, current_user, request.code)
    return {"message": "Email verified successfully"}


@router.post("/password-reset")
@limiter.limit("3/minute")
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset email"""
    message = AuthService.request_password_reset(db, request.email)
    return {"message": message}


@router.post("/password-reset/confirm")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    user = AuthService.reset_password(db, request.token, request.new_password)
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password"""
    user = AuthService.change_password(
        db, 
        current_user, 
        request.current_password, 
        request.new_password
    )
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user (client should remove tokens)"""
    return {"message": "Logged out successfully"}