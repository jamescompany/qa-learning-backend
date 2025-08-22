from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db
from schemas.todo import (
    TodoCreate,
    TodoUpdate,
    TodoResponse,
    TodoList,
    TodoStats
)
from dependencies import (
    get_current_user,
    PaginationParams
)
from models import User, Todo, TodoStatus, TodoPriority
from core.exceptions import TodoNotFoundException, InsufficientPermissionsException

router = APIRouter(prefix="/todos", tags=["Todos"])


@router.get("/", response_model=TodoList)
async def get_todos(
    pagination: PaginationParams = Depends(),
    status: Optional[TodoStatus] = Query(None, description="Filter by status"),
    priority: Optional[TodoPriority] = Query(None, description="Filter by priority"),
    is_archived: bool = Query(False, description="Include archived todos"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's todos with filters"""
    query = db.query(Todo).filter(Todo.user_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Todo.status == status)
    
    if priority:
        query = query.filter(Todo.priority == priority)
    
    if not is_archived:
        query = query.filter(Todo.is_archived == False)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            Todo.title.ilike(search_filter) | 
            Todo.description.ilike(search_filter)
        )
    
    # Apply sorting
    if pagination.sort_by == "due_date":
        order_column = Todo.due_date
    elif pagination.sort_by == "priority":
        order_column = Todo.priority
    elif pagination.sort_by == "status":
        order_column = Todo.status
    else:
        order_column = Todo.created_at
    
    if pagination.order == "asc":
        query = query.order_by(order_column.asc().nullslast())
    else:
        query = query.order_by(order_column.desc().nullslast())
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    todos = query.offset(pagination.offset).limit(pagination.limit).all()
    
    return {
        "todos": todos,
        "total": total,
        "page": pagination.page,
        "limit": pagination.limit
    }


@router.get("/stats", response_model=TodoStats)
async def get_todo_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get todo statistics for current user"""
    todos = db.query(Todo).filter(
        and_(
            Todo.user_id == current_user.id,
            Todo.is_archived == False
        )
    ).all()
    
    stats = {
        "total": len(todos),
        "todo": sum(1 for t in todos if t.status == TodoStatus.TODO),
        "in_progress": sum(1 for t in todos if t.status == TodoStatus.IN_PROGRESS),
        "done": sum(1 for t in todos if t.status == TodoStatus.DONE),
        "cancelled": sum(1 for t in todos if t.status == TodoStatus.CANCELLED)
    }
    
    return stats


@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo(
    todo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get todo by ID"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    return todo


@router.post("/", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    todo_create: TodoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new todo"""
    todo = Todo(
        title=todo_create.title,
        description=todo_create.description,
        priority=todo_create.priority,
        due_date=todo_create.due_date,
        user_id=current_user.id,
        status=TodoStatus.TODO
    )
    
    db.add(todo)
    db.commit()
    db.refresh(todo)
    
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update todo by ID"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    update_data = todo_update.dict(exclude_unset=True)
    
    # Track if status changes to done
    if "status" in update_data:
        if update_data["status"] == TodoStatus.DONE and todo.status != TodoStatus.DONE:
            update_data["completed_at"] = datetime.utcnow()
        elif update_data["status"] != TodoStatus.DONE:
            update_data["completed_at"] = None
    
    # Update todo fields
    for field, value in update_data.items():
        setattr(todo, field, value)
    
    db.commit()
    db.refresh(todo)
    
    return todo


@router.patch("/{todo_id}", response_model=TodoResponse)
async def patch_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Partially update todo by ID"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    update_data = todo_update.dict(exclude_unset=True)
    
    # Track if status changes to done
    if "status" in update_data:
        if update_data["status"] == TodoStatus.DONE and todo.status != TodoStatus.DONE:
            update_data["completed_at"] = datetime.utcnow()
        elif update_data["status"] != TodoStatus.DONE:
            update_data["completed_at"] = None
    
    # Update todo fields
    for field, value in update_data.items():
        setattr(todo, field, value)
    
    db.commit()
    db.refresh(todo)
    
    return todo


@router.patch("/{todo_id}/toggle", response_model=TodoResponse)
async def toggle_todo(
    todo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle todo completion status"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    # Toggle between TODO and DONE status
    if todo.status == TodoStatus.DONE:
        todo.status = TodoStatus.TODO
        todo.completed_at = None
    else:
        todo.status = TodoStatus.DONE
        todo.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(todo)
    
    return todo


@router.delete("/{todo_id}")
async def delete_todo(
    todo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete todo by ID"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    db.delete(todo)
    db.commit()
    
    return {"message": "Todo deleted successfully"}


@router.post("/{todo_id}/complete")
async def complete_todo(
    todo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark todo as completed"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    todo.status = TodoStatus.DONE
    todo.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(todo)
    
    return {"message": "Todo marked as completed", "completed_at": todo.completed_at}


@router.post("/{todo_id}/archive")
async def archive_todo(
    todo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive todo"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    todo.is_archived = True
    db.commit()
    
    return {"message": "Todo archived successfully"}


@router.post("/{todo_id}/unarchive")
async def unarchive_todo(
    todo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unarchive todo"""
    todo = db.query(Todo).filter(
        and_(
            Todo.id == todo_id,
            Todo.user_id == current_user.id
        )
    ).first()
    
    if not todo:
        raise TodoNotFoundException()
    
    todo.is_archived = False
    db.commit()
    
    return {"message": "Todo unarchived successfully"}


@router.post("/bulk-delete")
async def bulk_delete_todos(
    todo_ids: list[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete multiple todos"""
    deleted_count = db.query(Todo).filter(
        and_(
            Todo.id.in_(todo_ids),
            Todo.user_id == current_user.id
        )
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return {"message": f"{deleted_count} todos deleted successfully"}


@router.post("/bulk-update-status")
async def bulk_update_status(
    todo_ids: list[str],
    status: TodoStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update status for multiple todos"""
    update_data = {"status": status}
    
    if status == TodoStatus.DONE:
        update_data["completed_at"] = datetime.utcnow()
    else:
        update_data["completed_at"] = None
    
    updated_count = db.query(Todo).filter(
        and_(
            Todo.id.in_(todo_ids),
            Todo.user_id == current_user.id
        )
    ).update(update_data, synchronize_session=False)
    
    db.commit()
    
    return {"message": f"{updated_count} todos updated successfully"}