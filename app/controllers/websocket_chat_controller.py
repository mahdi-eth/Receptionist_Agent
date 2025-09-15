import json
import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.hotel_agent import hotel_agent

logger = logging.getLogger(__name__)


class WebSocketChatController:
    """WebSocket controller for real-time chat with the hotel agent"""
    
    def __init__(self):
        # Store active connections
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept WebSocket connection and store it"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def handle_connection(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket connection lifecycle"""
        await self.connect(websocket, session_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                await self.handle_message(websocket, session_id, message_data)
                
        except WebSocketDisconnect:
            self.disconnect(session_id)
        except Exception as e:
            logger.error(f"WebSocket error for session {session_id}: {e}")
            self.disconnect(session_id)
            await websocket.close()
    
    async def handle_message(self, websocket: WebSocket, session_id: str, message_data: Dict[str, Any]):
        """Handle incoming message from client"""
        try:
            message_type = message_data.get("type")
            
            if message_type == "start_session":
                await self._handle_start_session(websocket, session_id, message_data)
            elif message_type == "user_message":
                await self._handle_user_message(websocket, session_id, message_data)
            elif message_type == "end_session":
                await self._handle_end_session(websocket, session_id, message_data)
            else:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(websocket, "Failed to process message")
    
    async def _handle_start_session(self, websocket: WebSocket, session_id: str, message_data: Dict[str, Any]):
        """Handle session start request"""
        try:
            guest_info = message_data.get("guest_info")
            
            # Create session in agent
            success = await hotel_agent.create_session(session_id, guest_info)
            
            if success:
                await websocket.send_text(json.dumps({
                    "type": "session_started",
                    "session_id": session_id,
                    "message": "Welcome! I'm your virtual receptionist. How can I help you today? 😊"
                }))
            else:
                await self._send_error(websocket, "Failed to create session")
                
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            await self._send_error(websocket, "Failed to start session")
    
    async def _handle_user_message(self, websocket: WebSocket, session_id: str, message_data: Dict[str, Any]):
        """Handle user message and stream agent response"""
        try:
            user_message = message_data.get("message", "")
            if not user_message.strip():
                await self._send_error(websocket, "Empty message")
                return
            
            # Get database session directly
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                # Stream agent response
                async for chunk in hotel_agent.process_message_stream(session_id, user_message, db):
                    await websocket.send_text(json.dumps(chunk))
                    
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            await self._send_error(websocket, "Failed to process message")
    
    async def _handle_end_session(self, websocket: WebSocket, session_id: str, message_data: Dict[str, Any]):
        """Handle session end request"""
        try:
            success = await hotel_agent.end_session(session_id)
            
            await websocket.send_text(json.dumps({
                "type": "session_ended",
                "session_id": session_id,
                "success": success
            }))
            
            # Close WebSocket connection
            await websocket.close()
            self.disconnect(session_id)
            
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            await self._send_error(websocket, "Failed to end session")
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to client"""
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": error_message
            }))
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    def get_active_sessions(self) -> list[str]:
        """Get list of active session IDs"""
        return list(self.active_connections.keys())
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific session"""
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to session {session_id}: {e}")
                self.disconnect(session_id)


# Global instance
websocket_chat_controller = WebSocketChatController() 