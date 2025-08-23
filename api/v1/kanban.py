from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import get_db
from schemas.kanban import (
    BoardCreate,
    BoardUpdate,
    BoardResponse,
    BoardList,
    ColumnCreate,
    ColumnUpdate,
    ColumnResponse,
    CardCreate,
    CardUpdate,
    CardResponse,
    CardMoveRequest
)
from dependencies import get_current_user
from models import User, KanbanBoard, KanbanColumn, KanbanCard
from core.exceptions import BoardNotFoundException, InsufficientPermissionsException

router = APIRouter(prefix="/kanban", tags=["Kanban"])


@router.get("/boards", response_model=BoardList)
async def get_boards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's kanban boards"""
    boards = db.query(KanbanBoard).filter(KanbanBoard.user_id == current_user.id).all()
    
    return BoardList(
        boards=[BoardResponse.from_orm(board) for board in boards],
        total=len(boards)
    )


@router.get("/boards/{board_id}", response_model=BoardResponse)
async def get_board(
    board_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific kanban board with all columns and cards"""
    board = db.query(KanbanBoard).filter(
        and_(
            KanbanBoard.id == board_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not board:
        raise BoardNotFoundException(f"Board with id {board_id} not found")
    
    return BoardResponse.from_orm(board)


@router.post("/boards", response_model=BoardResponse, status_code=status.HTTP_201_CREATED)
async def create_board(
    board_data: BoardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new kanban board"""
    board = KanbanBoard(
        user_id=current_user.id,
        **board_data.dict()
    )
    
    db.add(board)
    db.commit()
    db.refresh(board)
    
    return BoardResponse.from_orm(board)


@router.patch("/boards/{board_id}", response_model=BoardResponse)
async def update_board(
    board_id: str,
    board_data: BoardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a kanban board"""
    board = db.query(KanbanBoard).filter(
        and_(
            KanbanBoard.id == board_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not board:
        raise BoardNotFoundException(f"Board with id {board_id} not found")
    
    for field, value in board_data.dict(exclude_unset=True).items():
        setattr(board, field, value)
    
    board.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(board)
    
    return BoardResponse.from_orm(board)


@router.delete("/boards/{board_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_board(
    board_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a kanban board"""
    board = db.query(KanbanBoard).filter(
        and_(
            KanbanBoard.id == board_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not board:
        raise BoardNotFoundException(f"Board with id {board_id} not found")
    
    db.delete(board)
    db.commit()
    
    return {"message": "Board deleted successfully"}


# Column endpoints
@router.post("/boards/{board_id}/columns", response_model=ColumnResponse, status_code=status.HTTP_201_CREATED)
async def create_column(
    board_id: str,
    column_data: ColumnCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new column in a board"""
    board = db.query(KanbanBoard).filter(
        and_(
            KanbanBoard.id == board_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not board:
        raise BoardNotFoundException(f"Board with id {board_id} not found")
    
    column = KanbanColumn(
        board_id=board_id,
        **column_data.dict()
    )
    
    db.add(column)
    db.commit()
    db.refresh(column)
    
    return ColumnResponse.from_orm(column)


@router.patch("/columns/{column_id}", response_model=ColumnResponse)
async def update_column(
    column_id: str,
    column_data: ColumnUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a column"""
    column = db.query(KanbanColumn).join(KanbanBoard).filter(
        and_(
            KanbanColumn.id == column_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")
    
    for field, value in column_data.dict(exclude_unset=True).items():
        setattr(column, field, value)
    
    column.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(column)
    
    return ColumnResponse.from_orm(column)


@router.delete("/columns/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_column(
    column_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a column"""
    column = db.query(KanbanColumn).join(KanbanBoard).filter(
        and_(
            KanbanColumn.id == column_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")
    
    db.delete(column)
    db.commit()
    
    return {"message": "Column deleted successfully"}


# Card endpoints
@router.post("/columns/{column_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    column_id: str,
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new card in a column"""
    column = db.query(KanbanColumn).join(KanbanBoard).filter(
        and_(
            KanbanColumn.id == column_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")
    
    card = KanbanCard(
        column_id=column_id,
        **card_data.dict()
    )
    
    db.add(card)
    db.commit()
    db.refresh(card)
    
    return CardResponse.from_orm(card)


@router.patch("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: str,
    card_data: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a card"""
    card = db.query(KanbanCard).join(KanbanColumn).join(KanbanBoard).filter(
        and_(
            KanbanCard.id == card_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    for field, value in card_data.dict(exclude_unset=True).items():
        setattr(card, field, value)
    
    card.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(card)
    
    return CardResponse.from_orm(card)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a card"""
    card = db.query(KanbanCard).join(KanbanColumn).join(KanbanBoard).filter(
        and_(
            KanbanCard.id == card_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    db.delete(card)
    db.commit()
    
    return {"message": "Card deleted successfully"}


@router.post("/cards/{card_id}/move", response_model=CardResponse)
async def move_card(
    card_id: str,
    move_request: CardMoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Move a card to a different column"""
    card = db.query(KanbanCard).join(KanbanColumn).join(KanbanBoard).filter(
        and_(
            KanbanCard.id == card_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    target_column = db.query(KanbanColumn).join(KanbanBoard).filter(
        and_(
            KanbanColumn.id == move_request.target_column_id,
            KanbanBoard.user_id == current_user.id
        )
    ).first()
    
    if not target_column:
        raise HTTPException(status_code=404, detail="Target column not found")
    
    card.column_id = move_request.target_column_id
    if move_request.position is not None:
        card.position = move_request.position
    
    card.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(card)
    
    return CardResponse.from_orm(card)