from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .posts import router as posts_router
from .todos import router as todos_router
from .comments import router as comments_router
from .files import router as files_router
from .websocket import router as websocket_router
from .calendar import router as calendar_router
from .kanban import router as kanban_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(posts_router)
api_router.include_router(todos_router)
api_router.include_router(comments_router)
api_router.include_router(files_router)
api_router.include_router(websocket_router)
api_router.include_router(calendar_router)
api_router.include_router(kanban_router)

__all__ = ["api_router"]