import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.hotel_agent import hotel_agent
from app.controllers.websocket_chat_controller import websocket_chat_controller

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Hotel Agent - LangGraph"])


@router.websocket("/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat with the hotel agent"""
    await websocket_chat_controller.handle_connection(websocket, session_id)


@router.post("/session/{session_id}/start")
async def start_agent_session(
    session_id: str,
    guest_info: Optional[Dict[str, Any]] = None
):
    """Start a new agent session (alternative to WebSocket start)"""
    try:
        success = await hotel_agent.create_session(session_id, guest_info)
        
        if success:
            return {
                "success": True,
                "session_id": session_id,
                "message": "Session started successfully",
                "guest_info_provided": guest_info is not None
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create session")
            
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start session")


@router.delete("/session/{session_id}")
async def end_agent_session(session_id: str):
    """End an agent session"""
    try:
        success = await hotel_agent.end_session(session_id)
        
        return {
            "success": success,
            "session_id": session_id,
            "message": "Session ended" if success else "Session not found"
        }
        
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end session")


@router.get("/session/{session_id}/info")
async def get_session_info(session_id: str):
    """Get information about a session"""
    try:
        session_info = hotel_agent.get_session_info(session_id)
        
        if session_info:
            return session_info
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session info")


@router.get("/sessions/active")
async def get_active_sessions():
    """Get list of active sessions"""
    try:
        agent_sessions = hotel_agent.list_active_sessions()
        websocket_sessions = websocket_chat_controller.get_active_sessions()
        
        return {
            "agent_sessions": agent_sessions,
            "websocket_sessions": websocket_sessions,
            "total_active": len(agent_sessions)
        }
        
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active sessions")


@router.post("/session/{session_id}/message")
async def send_message_to_session(
    session_id: str,
    message_data: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db)
):
    """Send a message to a session and get response (non-streaming alternative)"""
    try:
        message = message_data.get("message", "")
        if not message.strip():
            raise HTTPException(status_code=400, detail="Empty message")
        
        # Collect all streaming chunks into a single response
        response_parts = []
        status_updates = []
        
        async for chunk in hotel_agent.process_message_stream(session_id, message, db):
            if chunk.get("type") == "response":
                if chunk.get("complete"):
                    # This is the final complete response
                    return {
                        "success": True,
                        "response": chunk["content"],
                        "session_id": session_id,
                        "status_updates": status_updates
                    }
            elif chunk.get("type") == "status":
                status_updates.append(chunk["content"])
            elif chunk.get("type") == "error":
                raise HTTPException(status_code=500, detail=chunk["content"])
        
        # Fallback if no complete response was received
        raise HTTPException(status_code=500, detail="No complete response received")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.get("/health")
async def agent_health_check():
    """Check if the agent service is healthy"""
    try:
        # Check if the agent is properly initialized
        if hotel_agent.llm is None:
            return {
                "status": "unhealthy",
                "message": "LLM not initialized - check API key configuration",
                "agent_available": False
            }
        
        if hotel_agent.graph is None:
            return {
                "status": "partial",
                "message": "Graph not initialized but LLM available",
                "agent_available": True
            }
        
        return {
            "status": "healthy",
            "message": "Agent service is fully operational",
            "agent_available": True,
            "active_sessions": len(hotel_agent.list_active_sessions())
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "agent_available": False
        }


@router.get("/tools")
async def get_available_tools():
    """Get list of available tools for the agent"""
    try:
        tools_info = []
        if hotel_agent.tools:
            for tool_name, tool in hotel_agent.tools.items():
                tools_info.append({
                    "name": tool_name,
                    "description": tool.description
                })
        
        return {
            "tools": tools_info,
            "count": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting tools: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available tools") 