from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.chat_session_service import ChatSessionService
from app.schemas.chat import (
    ChatRequest, 
    ChatResponse, 
    ChatSessionResponse, 
    ChatSessionEnd,
    ChatSessionWithMessages
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Hotel Receptionist Agent"])


@router.post("/start", response_model=ChatSessionResponse, include_in_schema=True)
async def start_chat_session(
    request: Request,
    guest_id: Optional[int] = Query(None, description="Guest ID if known"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Start a new chat session with the hotel receptionist agent
    
    This endpoint creates a new chat session and returns the session ID.
    The guest_id is optional - if provided, the agent will have access to guest information.
    If not provided, the agent can still help with general inquiries and create new guest profiles.
    """
    try:
        chat_service = ChatSessionService()
        
        # Get client information
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Create chat session
        session = await chat_service.create_chat_session(
            guest_id=guest_id,
            ip_address=ip_address,
            user_agent=user_agent,
            context={
                "started_at": datetime.now().isoformat(),
                "guest_id": guest_id,
                "session_type": "receptionist_chat"
            }
        )
        
        logger.info(f"Started chat session {session.session_id} for guest {guest_id}")
        
        return ChatSessionResponse(
            id=session.id,
            session_id=session.session_id,
            guest_id=session.guest_id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            status=session.status,
            context=session.context,
            created_at=session.created_at,
            updated_at=session.updated_at,
            ended_at=session.ended_at
        )
        
    except Exception as e:
        logger.error(f"Error starting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start chat session")


@router.post("/message", response_model=ChatResponse, include_in_schema=True)
async def send_message(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a message to the hotel receptionist agent
    
    This endpoint processes user messages and returns the agent's response.
    The agent can:
    - Answer questions about hotel services and amenities
    - Help with room bookings and reservations
    - Create and update guest profiles
    - Provide information about room availability
    - Handle check-in and check-out processes
    
    If no session_id is provided, a new session will be created automatically.
    """
    try:
        chat_service = ChatSessionService()
        
        # If no session_id provided, create a new one
        if not chat_request.session_id:
            session = await chat_service.create_chat_session(
                guest_id=chat_request.guest_id
            )
            session_id = session.session_id
        else:
            session_id = chat_request.session_id
            
            # Verify session exists and is active
            session = await chat_service.get_chat_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Chat session not found")
            if session.status != "active":
                raise HTTPException(status_code=400, detail="Chat session is not active")
        
        # Process the message
        response = await chat_service.process_user_message(
            session_id, 
            chat_request.message, 
            db
        )
        
        logger.info(f"Processed message in session {session_id}")
        
        return ChatResponse(
            message=response,
            session_id=session_id,
            guest_id=chat_request.guest_id,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")


@router.get("/session/{session_id}", response_model=ChatSessionWithMessages, include_in_schema=True)
async def get_chat_session(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get chat session information and message history
    
    This endpoint retrieves the complete chat session including all messages.
    Useful for displaying chat history or resuming conversations.
    """
    try:
        chat_service = ChatSessionService()
        
        session = await chat_service.get_chat_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get conversation history
        conversation_history = await chat_service.get_conversation_history(session_id)
        
        # Convert to response format
        messages = []
        for msg in conversation_history:
            messages.append({
                "id": 0,  # We don't have individual message IDs in this format
                "session_id": session.id,
                "content": msg["content"],
                "role": msg["role"],
                "message_type": msg["role"],
                "timestamp": datetime.now(),  # We don't have individual timestamps in this format
                "message_metadata": {}
            })
        
        return ChatSessionWithMessages(
            id=session.id,
            session_id=session.session_id,
            guest_id=session.guest_id,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            status=session.status,
            context=session.context,
            created_at=session.created_at,
            updated_at=session.updated_at,
            ended_at=session.ended_at,
            messages=messages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat session")


@router.post("/session/{session_id}/end", response_model=dict, include_in_schema=True)
async def end_chat_session(
    session_id: str,
    end_request: ChatSessionEnd,
    db: AsyncSession = Depends(get_async_db)
):
    """
    End a chat session
    
    This endpoint marks a chat session as ended and cleans up resources.
    The session will no longer accept new messages.
    """
    try:
        chat_service = ChatSessionService()
        
        success = await chat_service.end_chat_session(
            session_id, 
            end_request.reason
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        logger.info(f"Ended chat session {session_id}")
        
        return {
            "success": True,
            "message": "Chat session ended successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to end chat session")


@router.get("/session/{session_id}/summary", response_model=dict, include_in_schema=True)
async def get_session_summary(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a summary of the chat session
    
    This endpoint provides statistics and metadata about the chat session,
    including message counts, duration, and context information.
    """
    try:
        chat_service = ChatSessionService()
        
        summary = await chat_service.get_session_summary(session_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get session summary")


@router.get("/tools", response_model=list, include_in_schema=True)
async def get_available_tools():
    """
    Get list of available tools for the agent
    
    This endpoint returns information about all the tools the AI agent can use
    to help guests with their requests.
    """
    try:
        from app.services.agent_tools_service import AgentToolsService
        tools_service = AgentToolsService()
        tools = await tools_service.get_available_tools()
        return tools
        
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(status_code=500, detail="Failed to get available tools") 