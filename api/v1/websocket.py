from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from core import verify_token
from models import User
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.user_connections[id(websocket)] = user_id
        
        logger.info(f"User {user_id} connected via WebSocket")
        
        # Send connection confirmation
        await self.send_personal_message(
            {
                "type": "connection",
                "message": "Connected successfully",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )
    
    def disconnect(self, websocket: WebSocket):
        websocket_id = id(websocket)
        
        if websocket_id in self.user_connections:
            user_id = self.user_connections[websocket_id]
            
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            del self.user_connections[websocket_id]
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to websocket: {e}")
    
    async def send_user_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
    
    async def broadcast(self, message: dict, exclude_user: str = None):
        for user_id, connections in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")
    
    async def send_to_group(self, message: dict, user_ids: list[str]):
        for user_id in user_ids:
            await self.send_user_message(message, user_id)


manager = ConnectionManager()


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db)
):
    try:
        # Verify token and get user
        user_id = verify_token(token, "access")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            await websocket.close(code=4001, reason="Unauthorized")
            return
        
        # Connect user
        await manager.connect(websocket, user_id)
        
        # Handle messages
        try:
            while True:
                data = await websocket.receive_json()
                await handle_websocket_message(data, user, db)
        
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error for user {user_id}: {e}")
            manager.disconnect(websocket)
            await websocket.close(code=4000, reason="Error")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4001, reason="Unauthorized")


async def handle_websocket_message(data: dict, user: User, db: Session):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")
    
    if message_type == "ping":
        # Respond to ping
        await manager.send_user_message(
            {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            },
            user.id
        )
    
    elif message_type == "chat":
        # Handle chat message
        message_content = data.get("message", "")
        recipient_id = data.get("recipient_id")
        
        message_data = {
            "type": "chat",
            "sender_id": user.id,
            "sender_name": user.username,
            "message": message_content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if recipient_id:
            # Send to specific user
            await manager.send_user_message(message_data, recipient_id)
            # Send confirmation to sender
            await manager.send_user_message(
                {**message_data, "status": "sent"},
                user.id
            )
        else:
            # Broadcast to all connected users
            await manager.broadcast(message_data, exclude_user=user.id)
    
    elif message_type == "notification":
        # Handle notification
        notification_type = data.get("notification_type")
        notification_data = data.get("data", {})
        
        await handle_notification(notification_type, notification_data, user, db)
    
    elif message_type == "presence":
        # Update user presence
        status = data.get("status", "online")
        
        await manager.broadcast(
            {
                "type": "presence",
                "user_id": user.id,
                "username": user.username,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=user.id
        )
    
    else:
        # Unknown message type
        await manager.send_user_message(
            {
                "type": "error",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.utcnow().isoformat()
            },
            user.id
        )


async def handle_notification(
    notification_type: str,
    data: dict,
    user: User,
    db: Session
):
    """Handle different types of notifications"""
    
    if notification_type == "post_published":
        # Notify followers about new post
        post_id = data.get("post_id")
        post_title = data.get("title")
        
        # Get followers (simplified - you'd need a follower system)
        notification_data = {
            "type": "notification",
            "notification_type": "post_published",
            "data": {
                "post_id": post_id,
                "title": post_title,
                "author_id": user.id,
                "author_name": user.username
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Broadcast to all for now
        await manager.broadcast(notification_data, exclude_user=user.id)
    
    elif notification_type == "comment_added":
        # Notify post author about new comment
        post_author_id = data.get("post_author_id")
        post_id = data.get("post_id")
        comment_id = data.get("comment_id")
        
        if post_author_id and post_author_id != user.id:
            await manager.send_user_message(
                {
                    "type": "notification",
                    "notification_type": "comment_added",
                    "data": {
                        "post_id": post_id,
                        "comment_id": comment_id,
                        "commenter_id": user.id,
                        "commenter_name": user.username
                    },
                    "timestamp": datetime.utcnow().isoformat()
                },
                post_author_id
            )
    
    elif notification_type == "todo_reminder":
        # Send todo reminder
        todo_id = data.get("todo_id")
        todo_title = data.get("title")
        
        await manager.send_user_message(
            {
                "type": "notification",
                "notification_type": "todo_reminder",
                "data": {
                    "todo_id": todo_id,
                    "title": todo_title
                },
                "timestamp": datetime.utcnow().isoformat()
            },
            user.id
        )


# Utility functions for sending notifications from other parts of the app
async def notify_user(user_id: str, notification: dict):
    """Send notification to specific user"""
    await manager.send_user_message(
        {
            "type": "notification",
            **notification,
            "timestamp": datetime.utcnow().isoformat()
        },
        user_id
    )


async def broadcast_notification(notification: dict, exclude_user: str = None):
    """Broadcast notification to all connected users"""
    await manager.broadcast(
        {
            "type": "notification",
            **notification,
            "timestamp": datetime.utcnow().isoformat()
        },
        exclude_user
    )


async def get_online_users() -> list[str]:
    """Get list of currently online user IDs"""
    return list(manager.active_connections.keys())