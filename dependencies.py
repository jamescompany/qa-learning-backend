from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from database import get_db
from core import settings, verify_token
from core.exceptions import UnauthorizedException, UserNotFoundException
from models import User
import redis
from slowapi import Limiter
from slowapi.util import get_remote_address


# HTTPBearer for Swagger UI and API authentication
http_bearer = HTTPBearer(auto_error=True)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"] if settings.RATE_LIMIT_ENABLED else []
)


def get_redis_client() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from HTTPBearer token"""
    token = credentials.credentials
    
    try:
        user_id = verify_token(token, "access")
    except JWTError:
        raise UnauthorizedException(detail="Could not validate credentials")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundException()
    
    if user.is_deleted:
        raise UserNotFoundException()  # Don't reveal that account was deleted
    
    if not user.is_active:
        raise UnauthorizedException(detail="User account is inactive")
    
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None"""
    if not credentials:
        return None
    
    try:
        user_id = verify_token(credentials.credentials, "access")
    except JWTError:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted or not user.is_active:
        return None
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


class PaginationParams:
    def __init__(
        self,
        page: int = 1,
        limit: int = settings.PAGINATION_DEFAULT_LIMIT,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ):
        self.page = max(1, page)
        self.limit = min(limit, settings.PAGINATION_MAX_LIMIT)
        self.offset = (self.page - 1) * self.limit
        self.sort_by = sort_by
        self.order = order.lower() if order.lower() in ["asc", "desc"] else "desc"


class QueryParams:
    def __init__(
        self,
        q: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        author_id: Optional[str] = None
    ):
        self.q = q
        self.status = status
        self.tag = tag
        self.author_id = author_id