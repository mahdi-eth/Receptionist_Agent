from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.simple_chat_service import SimpleChatService
from app.schemas.chat import ChatRequest, ChatResponse
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/streaming-chat", tags=["Streaming Hotel Receptionist Agent"])


@router.post("/start", response_model=dict, include_in_schema=True)
async def start_chat_session(
    request: Request,
    guest_id: Optional[int] = Query(None, description="Guest ID if known")
):
    """
    Start a new streaming chat session with the hotel receptionist agent
    
    This endpoint creates a new chat session ID without storing anything in the database.
    The guest_id is optional - if provided, the agent will have access to guest information.
    """
    try:
        chat_service = SimpleChatService()
        session_id = chat_service.create_chat_session(guest_id)
        
        logger.info(f"Started streaming chat session {session_id} for guest {guest_id}")
        
        return {
            "session_id": session_id,
            "guest_id": guest_id,
            "message": "Chat session started successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting streaming chat session: {e}")
        raise HTTPException(status_code=500, detail="Failed to start chat session")


@router.post("/message", response_model=ChatResponse, include_in_schema=True)
async def send_message(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a message to the hotel receptionist agent (non-streaming)
    
    This endpoint processes user messages and returns the agent's response.
    The agent can help with room bookings, guest management, and hotel services.
    """
    try:
        chat_service = SimpleChatService()
        
        # If no session_id provided, create a new one
        if not chat_request.session_id:
            session_id = chat_service.create_chat_session(chat_request.guest_id)
        else:
            session_id = chat_request.session_id
        
        # Process the message
        response = await chat_service.process_user_message(
            session_id, 
            chat_request.message, 
            db
        )
        
        logger.info(f"Processed message in streaming session {session_id}")
        
        return ChatResponse(
            message=response,
            session_id=session_id,
            guest_id=chat_request.guest_id,
            timestamp=datetime.now()
        )
        
    except ValueError as e:
        logger.error(f"Service configuration error: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error processing streaming message: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to process message. Please try again later."
        )


@router.post("/message/stream")
async def send_message_stream(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a message to the hotel receptionist agent (streaming response)
    
    This endpoint processes user messages and streams the agent's response in real-time.
    Perfect for creating a more engaging chat experience.
    """
    try:
        chat_service = SimpleChatService()
        
        # If no session_id provided, create a new one
        if not chat_request.session_id:
            session_id = chat_service.create_chat_session(chat_request.guest_id)
        else:
            session_id = chat_request.session_id
        
        async def generate_stream():
            try:
                # Send initial message
                yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
                
                # Stream the response
                async for chunk in chat_service.process_user_message_stream(
                    session_id, 
                    chat_request.message, 
                    db
                ):
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # Send completion message
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
                
            except ValueError as e:
                error_msg = f"Service configuration error: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            }
        )
        
    except ValueError as e:
        logger.error(f"Service configuration error: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating streaming response: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to create streaming response. Please try again later."
        )


@router.get("/tools", response_model=list, include_in_schema=True)
async def get_available_tools():
    """
    Get list of available tools for the agent
    
    This endpoint returns information about all the tools the AI agent can use
    to help guests with their requests.
    """
    try:
        chat_service = SimpleChatService()
        tools = await chat_service.get_available_tools()
        return tools
        
    except ValueError as e:
        logger.error(f"Service configuration error: {e}")
        raise HTTPException(
            status_code=503, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to get available tools. Please try again later."
        )


@router.post("/test")
async def test_chat_service():
    """
    Test endpoint to verify the chat service is working
    
    This endpoint tests the basic functionality without requiring a database connection.
    """
    try:
        chat_service = SimpleChatService()
        
        # Test service initialization
        if not chat_service.gemini_service:
            return {
                "status": "error",
                "message": "Gemini service not available",
                "details": "Check your GEMINI_API_KEY configuration in .env file"
            }
        
        if not chat_service.agent_tools_service:
            return {
                "status": "error", 
                "message": "Agent tools service not available",
                "details": "Check your database connection and configuration"
            }
        
        return {
            "status": "success",
            "message": "Chat service is working correctly",
            "services": {
                "gemini": "available",
                "agent_tools": "available"
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing chat service: {e}")
        return {
            "status": "error",
            "message": f"Chat service test failed: {str(e)}"
        } 