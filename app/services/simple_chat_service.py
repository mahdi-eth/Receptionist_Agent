import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.gemini_service import GeminiService
from app.services.agent_tools_service import AgentToolsService
import logging

logger = logging.getLogger(__name__)


class SimpleChatService:
    """Simplified chat service that doesn't persist messages to database"""
    
    def __init__(self):
        try:
            self.gemini_service = GeminiService()
            self.agent_tools_service = AgentToolsService()
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            self.gemini_service = None
            self.agent_tools_service = None

    def create_chat_session(self, guest_id: Optional[int] = None) -> str:
        """Create a new chat session ID (no database storage)"""
        session_id = str(uuid.uuid4())
        logger.info(f"Created chat session {session_id} for guest {guest_id}")
        return session_id

    async def process_user_message(
        self, 
        session_id: str, 
        user_message: str,
        db: AsyncSession
    ) -> str:
        """Process a user message and generate a response"""
        try:
            # Check if services are available
            if not self.gemini_service:
                raise ValueError("Gemini service not available")
            
            if not self.agent_tools_service:
                raise ValueError("Agent tools service not available")
            
            # Simple conversation context (in-memory only)
            conversation_history = [
                {"role": "user", "content": user_message}
            ]
            
            # Generate response using Gemini
            response = await self.gemini_service.generate_response(
                user_message, 
                conversation_history,
                {"session_id": session_id}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            raise e

    async def process_user_message_stream(
        self, 
        session_id: str, 
        user_message: str,
        db: AsyncSession
    ) -> AsyncGenerator[str, None]:
        """Process a user message and stream the response"""
        try:
            # Check if services are available
            if not self.gemini_service:
                raise ValueError("Gemini service not available")
            
            if not self.agent_tools_service:
                raise ValueError("Agent tools service not available")
            
            # Simple conversation context (in-memory only)
            conversation_history = [
                {"role": "user", "content": user_message}
            ]
            
            # Generate response using Gemini
            response = await self.gemini_service.generate_response(
                user_message, 
                conversation_history,
                {"session_id": session_id}
            )
            
            # Stream the response word by word for better UX
            words = response.split()
            for word in words:
                yield word + " "
                # Small delay to simulate streaming
                import asyncio
                await asyncio.sleep(0.05)
            
        except Exception as e:
            logger.error(f"Error processing user message stream: {e}")
            raise e

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools for the agent"""
        try:
            if not self.agent_tools_service:
                raise ValueError("Agent tools service not available")
            return await self.agent_tools_service.get_available_tools()
        except Exception as e:
            logger.error(f"Error getting available tools: {e}")
            raise e

    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        try:
            if not self.agent_tools_service:
                raise ValueError("Agent tools service not available")
            
            return await self.agent_tools_service.execute_tool(tool_name, parameters, db)
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise e 