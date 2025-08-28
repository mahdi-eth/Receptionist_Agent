import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.chat_session import ChatSession, ChatMessage
from app.schemas.chat import ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate
from app.services.gemini_service import GeminiService
from app.services.agent_tools_service import AgentToolsService
from app.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)


class ChatSessionService:
    """Service for managing chat sessions and conversations"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.agent_tools_service = AgentToolsService()

    async def create_chat_session(
        self, 
        guest_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ChatSession:
        """Create a new chat session"""
        async with AsyncSessionLocal() as db:
            session_id = str(uuid.uuid4())
            
            session_data = ChatSessionCreate(
                session_id=session_id,
                guest_id=guest_id,
                ip_address=ip_address,
                user_agent=user_agent,
                context=context or {}
            )
            
            db_session = ChatSession(**session_data.model_dump())
            db.add(db_session)
            await db.commit()
            await db.refresh(db_session)
            
            # Add initial system message
            await self._add_system_message(db, db_session.id, "Chat session started")
            
            logger.info(f"Created chat session {session_id} for guest {guest_id}")
            return db_session

    async def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            return result.scalar_one_or_none()

    async def add_user_message(
        self, 
        session_id: str, 
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add a user message to the chat session"""
        async with AsyncSessionLocal() as db:
            session = await self.get_chat_session(session_id)
            if not session:
                raise ValueError(f"Chat session {session_id} not found")
            
            message_data = ChatMessageCreate(
                session_id=session.id,
                content=message,
                role="user",
                message_type="user",
                message_metadata=metadata or {}
            )
            
            db_message = ChatMessage(**message_data.model_dump())
            db.add(db_message)
            await db.commit()
            await db.refresh(db_message)
            
            logger.info(f"Added user message to session {session_id}")
            return db_message

    async def add_assistant_message(
        self, 
        session_id: str, 
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add an assistant message to the chat session"""
        async with AsyncSessionLocal() as db:
            session = await self.get_chat_session(session_id)
            if not session:
                raise ValueError(f"Chat session {session_id} not found")
            
            message_data = ChatMessageCreate(
                session_id=session.id,
                content=message,
                role="assistant",
                message_type="assistant",
                message_metadata=metadata or {}
            )
            
            db_message = ChatMessage(**message_data.model_dump())
            db.add(db_message)
            await db.commit()
            await db.refresh(db_message)
            
            logger.info(f"Added assistant message to session {session_id}")
            return db_message

    async def _add_system_message(
        self, 
        db: AsyncSession, 
        session_id: int, 
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add a system message to the chat session"""
        message_data = ChatMessageCreate(
            session_id=session_id,
            content=message,
            role="system",
            message_type="system",
            message_metadata=metadata or {}
        )
        
        db_message = ChatMessage(**message_data.model_dump())
        db.add(db_message)
        await db.commit()
        await db.refresh(db_message)
        
        return db_message

    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """Get conversation history for a session"""
        async with AsyncSessionLocal() as db:
            session = await self.get_chat_session(session_id)
            if not session:
                return []
            
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.timestamp.desc())
                .limit(limit)
            )
            
            messages = result.scalars().all()
            
            # Convert to format expected by Gemini
            conversation_history = []
            for msg in reversed(messages):  # Reverse to get chronological order
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            return conversation_history

    async def process_user_message(
        self, 
        session_id: str, 
        user_message: str,
        db: AsyncSession
    ) -> str:
        """Process a user message and generate a response"""
        try:
            # Add user message to session
            await self.add_user_message(session_id, user_message)
            
            # Get conversation history
            conversation_history = await self.get_conversation_history(session_id)
            
            # Get session context
            session = await self.get_chat_session(session_id)
            context = session.context if session else {}
            
            # Analyze user intent
            intent_analysis = await self.gemini_service.analyze_intent(user_message)
            
            # Get available tools
            available_tools = await self.agent_tools_service.get_available_tools()
            
            # Generate tool calls if needed
            tool_calls = await self.gemini_service.generate_tool_calls(user_message, available_tools)
            
            # Execute tools if needed
            tool_results = []
            if tool_calls:
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool")
                    parameters = tool_call.get("parameters", {})
                    
                    if tool_name:
                        result = await self.agent_tools_service.execute_tool(
                            tool_name, parameters, db
                        )
                        tool_results.append({
                            "tool": tool_name,
                            "result": result
                        })
            
            # Generate response with context
            response = await self.gemini_service.generate_response(
                user_message, 
                conversation_history,
                {
                    "intent": intent_analysis,
                    "tool_results": tool_results,
                    "session_context": context
                }
            )
            
            # Add assistant response to session
            await self.add_assistant_message(session_id, response)
            
            # Update session context with new information
            if session:
                new_context = context.copy()
                new_context.update({
                    "last_intent": intent_analysis.get("intent"),
                    "last_entities": intent_analysis.get("entities", {}),
                    "tools_used": [tr["tool"] for tr in tool_results],
                    "last_interaction": "user_message_processed"
                })
                
                await self._update_session_context(session_id, new_context)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            error_response = "I apologize, but I'm experiencing technical difficulties. Please try again or contact our staff directly."
            
            # Add error response to session
            await self.add_assistant_message(session_id, error_response)
            
            return error_response

    async def _update_session_context(
        self, 
        session_id: str, 
        context: Dict[str, Any]
    ):
        """Update session context"""
        async with AsyncSessionLocal() as db:
            session = await self.get_chat_session(session_id)
            if session:
                session.context = context
                await db.commit()

    async def end_chat_session(
        self, 
        session_id: str, 
        reason: Optional[str] = None
    ) -> bool:
        """End a chat session"""
        async with AsyncSessionLocal() as db:
            session = await self.get_chat_session(session_id)
            if not session:
                return False
            
            # Add system message about session ending
            await self._add_system_message(
                db, 
                session.id, 
                f"Chat session ended. Reason: {reason or 'User ended session'}"
            )
            
            # Update session status
            session.status = "ended"
            session.ended_at = db.func.now()
            
            await db.commit()
            
            logger.info(f"Ended chat session {session_id}")
            return True

    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of the chat session"""
        async with AsyncSessionLocal() as db:
            session = await self.get_chat_session(session_id)
            if not session:
                return {}
            
            # Get message count
            result = await db.execute(
                select(ChatMessage).where(ChatMessage.session_id == session.id)
            )
            messages = result.scalars().all()
            
            user_messages = [m for m in messages if m.role == "user"]
            assistant_messages = [m for m in messages if m.role == "assistant"]
            
            return {
                "session_id": session.session_id,
                "guest_id": session.guest_id,
                "status": session.status,
                "created_at": session.created_at,
                "ended_at": session.ended_at,
                "total_messages": len(messages),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "context": session.context,
                "duration_minutes": None  # Could calculate if needed
            } 