from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserResponse, UserUpdate, UserList, UserCreate
from services import UserService
from dependencies import (
    get_current_user,
    get_current_admin_user,
    PaginationParams
)
from models import User, UserRole

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user information"""
    updated_user = UserService.update_user(db, current_user.id, user_update)
    return updated_user


@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account"""
    UserService.delete_user(db, current_user.id)
    return {"message": "User account deleted successfully"}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    user = UserService.get_user(db, user_id)
    return user


@router.get("/username/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    db: Session = Depends(get_db)
):
    """Get user by username"""
    user = UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/", response_model=UserList)
async def get_users(
    pagination: PaginationParams = Depends(),
    search: Optional[str] = Query(None, description="Search by email, username, or name"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    db: Session = Depends(get_db)
):
    """Get list of users with optional filters"""
    users = UserService.get_users(
        db,
        skip=pagination.offset,
        limit=pagination.limit,
        search=search,
        role=role,
        is_active=is_active,
        is_verified=is_verified
    )
    
    total = UserService.count_users(
        db,
        search=search,
        role=role,
        is_active=is_active,
        is_verified=is_verified
    )
    
    return {
        "users": users,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


# Admin endpoints

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_create: UserCreate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)"""
    user = UserService.create_user(db, user_create)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user by ID (Admin only)"""
    updated_user = UserService.update_user(db, user_id, user_update)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user by ID (Admin only)"""
    UserService.delete_user(db, user_id)
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate user account (Admin only)"""
    user = UserService.activate_user(db, user_id)
    return {"message": f"User {user.email} activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account (Admin only)"""
    user = UserService.deactivate_user(db, user_id)
    return {"message": f"User {user.email} deactivated successfully"}


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user role (Admin only)"""
    user = UserService.update_user_role(db, user_id, role)
    return {"message": f"User {user.email} role updated to {role}"}