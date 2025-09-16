import json
import uuid
import asyncio
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator, Annotated
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# Local imports
from app.services.guest_service import GuestService
from app.services.room_service import RoomService
from app.services.reservation_service import ReservationService
from app.schemas.guest import GuestCreate, GuestUpdate
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from app.config import settings

logger = logging.getLogger(__name__)


# ===== PYDANTIC MODELS =====
class GuestInfo(BaseModel):
    """Guest information structure"""

    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    nationality: Optional[str] = None
    passport_number: Optional[str] = None


class AgentState(BaseModel):
    """State for the LangGraph agent"""

    messages: List[Any] = Field(default_factory=list)
    session_id: str
    guest_info: Optional[GuestInfo] = None
    conversation_context: Dict[str, Any] = Field(default_factory=dict)
    tools_used: List[str] = Field(default_factory=list)
    current_task: str = ""
    last_action: str = ""


# ===== TOOL DEFINITIONS =====
class CreateGuestTool(BaseTool):
    """Tool to create a new guest"""

    name = "create_guest"
    description = "Create a new guest profile with provided information"
    guest_service: GuestService = Field(exclude=True)  # Exclude from serialization

    def _run(self, **kwargs) -> Dict[str, Any]:
        """Synchronous run method"""
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs) -> Dict[str, Any]:
        try:
            guest_data = GuestCreate(**kwargs)
            # We need to get the db session from somewhere - for now, we'll handle this in the agent
            return {
                "success": True,
                "action": "create_guest",
                "data": kwargs,
                "message": "Guest information captured successfully!",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class SearchRoomsTool(BaseTool):
    """Tool to search for available rooms"""

    name = "search_rooms"
    description = "Search for available rooms by type, dates, and other criteria"
    room_service: RoomService = Field(exclude=True)  # Exclude from serialization

    def _run(self, room_type: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Synchronous run method"""
        return asyncio.run(self._arun(room_type=room_type, **kwargs))

    async def _arun(self, room_type: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            return {
                "success": True,
                "action": "search_rooms",
                "data": {"room_type": room_type, **kwargs},
                "message": f"🔍 Found available {room_type or 'rooms'}! Let me show you the options...",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class CreateReservationTool(BaseTool):
    """Tool to create a reservation"""

    name = "create_reservation"
    description = "Create a new reservation for a guest"
    reservation_service: ReservationService = Field(
        exclude=True
    )  # Exclude from serialization

    def _run(self, **kwargs) -> Dict[str, Any]:
        """Synchronous run method"""
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs) -> Dict[str, Any]:
        try:
            return {
                "success": True,
                "action": "create_reservation",
                "data": kwargs,
                "message": "🎉 Creating your reservation now...",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# ===== MAIN AGENT CLASS =====
class HotelAgent:
    """Unified LangGraph-based hotel agent"""

    def __init__(self):
        self.sessions: Dict[str, AgentState] = {}  # In-memory session storage
        self.llm = None
        self.guest_service = GuestService()
        self.room_service = RoomService()
        self.reservation_service = ReservationService()
        self.graph = None

        # Initialize LLM and tools
        self._init_llm()
        self._init_tools()
        self._build_graph()

    def _init_llm(self):
        """Initialize the language model"""
        try:
            if not settings.gemini_api_key:
                logger.warning("GEMINI_API_KEY not configured")
                return

            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=settings.gemini_api_key,
                temperature=0.7,
                streaming=True,
            )
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")

    def _init_tools(self):
        """Initialize agent tools"""
        self.tools = {
            "create_guest": CreateGuestTool(guest_service=self.guest_service),
            "search_rooms": SearchRoomsTool(room_service=self.room_service),
            "create_reservation": CreateReservationTool(
                reservation_service=self.reservation_service
            ),
        }

    def _build_graph(self):
        """Build the LangGraph conversation flow"""
        if not self.llm:
            return

        # Define the conversation flow with a simpler dict-based state
        from typing_extensions import TypedDict

        class GraphState(TypedDict):
            messages: List[Dict[str, str]]
            session_id: str
            current_task: str
            last_action: str
            response: str

        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("analyze_message", self._analyze_message_simple)
        workflow.add_node("execute_tools", self._execute_tools_simple)
        workflow.add_node("generate_response", self._generate_response_simple)

        # Define edges
        workflow.set_entry_point("analyze_message")
        workflow.add_edge("analyze_message", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)

        self.graph = workflow.compile()

    async def create_session(
        self, session_id: str, guest_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create a new conversation session"""
        try:
            guest_data = None
            if guest_info:
                guest_data = GuestInfo(**guest_info)

            self.sessions[session_id] = AgentState(
                session_id=session_id,
                guest_info=guest_data,
                messages=[],
                conversation_context={
                    "created_at": datetime.now().isoformat(),
                    "has_guest_info": guest_data is not None,
                },
            )

            logger.info(
                f"Created session {session_id} with guest info: {guest_data is not None}"
            )
            return True

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    async def end_session(self, session_id: str) -> bool:
        """End a conversation session"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Ended session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return False

    async def process_message_stream(
        self, session_id: str, message: str, db: AsyncSession
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a message and stream the response"""
        try:
            if session_id not in self.sessions:
                yield {
                    "type": "error",
                    "content": "Session not found. Please start a new conversation.",
                }
                return

            if not self.graph or not self.llm:
                yield {
                    "type": "error",
                    "content": "Agent service not available. Please try again later.",
                }
                return

            state = self.sessions[session_id]

            # Add user message to state
            state.messages.append(HumanMessage(content=message))

            # Process through the graph
            async for chunk in self._process_with_graph(state, db):
                yield chunk

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield {
                "type": "error",
                "content": "I apologize, but I'm experiencing technical difficulties. Please try again.",
            }

    async def _process_with_graph(
        self, state: AgentState, db: AsyncSession
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process message through the LangGraph workflow"""
        try:
            # Stream status update
            yield {"type": "status", "content": "🤔 Thinking..."}

            # Prepare graph state
            last_message = state.messages[-1].content if state.messages else ""
            graph_state = {
                "messages": [{"role": "user", "content": last_message}],
                "session_id": state.session_id,
                "current_task": "",
                "last_action": "",
                "response": "",
            }

            # Run the graph
            result = None
            if self.graph:
                result = await self.graph.ainvoke(graph_state)
                response_text = result.get(
                    "response", "I'm sorry, I couldn't process your request."
                )
            else:
                # Fallback without graph
                response_text = await self._simple_response(last_message, state)

            # Show action status if available
            if result and result.get("last_action"):
                yield {"type": "status", "content": result["last_action"]}
                await asyncio.sleep(0.5)

            # Stream the final response
            if response_text:
                # Stream word by word for better UX
                words = response_text.split()

                for word in words:
                    yield {"type": "response", "content": word + " ", "partial": True}
                    await asyncio.sleep(0.05)  # Slight delay for streaming effect

                # Final complete response
                yield {
                    "type": "response",
                    "content": response_text,
                    "partial": False,
                    "complete": True,
                }

        except Exception as e:
            logger.error(f"Error in graph processing: {e}")
            yield {
                "type": "error",
                "content": "I encountered an issue while processing your request.",
            }

    def _analyze_message_simple(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the user message and determine intent"""
        try:
            last_message = state["messages"][-1]["content"] if state["messages"] else ""

            # Simple intent analysis (can be enhanced)
            state["current_task"] = "respond"
            if any(
                word in last_message.lower()
                for word in ["book", "reserve", "reservation"]
            ):
                state["current_task"] = "booking"
            elif any(
                word in last_message.lower() for word in ["room", "available", "check"]
            ):
                state["current_task"] = "room_inquiry"
            elif any(
                word in last_message.lower() for word in ["name", "email", "info"]
            ):
                state["current_task"] = "collect_info"

            return state

        except Exception as e:
            logger.error(f"Error analyzing message: {e}")
            return state

    def _execute_tools_simple(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute relevant tools based on the current task"""
        try:
            if state["current_task"] == "room_inquiry":
                state["last_action"] = "🔍 Checking room availability..."

            elif state["current_task"] == "booking":
                state["last_action"] = "📝 Preparing reservation..."

            elif state["current_task"] == "collect_info":
                state["last_action"] = "📋 Collecting guest information..."
            else:
                state["last_action"] = "💭 Processing your request..."

            return state

        except Exception as e:
            logger.error(f"Error executing tools: {e}")
            return state

    async def _generate_response_simple(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final response using LLM"""
        try:
            session_id = state["session_id"]
            session_state = self.sessions.get(session_id)

            if not session_state:
                state["response"] = "Session not found."
                return state

            # Build context for the LLM
            system_prompt = self._build_system_prompt(session_state)

            # Get the last user message
            last_message = state["messages"][-1]["content"] if state["messages"] else ""

            # Prepare messages for LLM - simple format
            conversation = (
                f"System: {system_prompt}\n\nUser: {last_message}\n\nAssistant:"
            )

            # Generate response
            if self.llm:
                response = await self.llm.ainvoke([HumanMessage(content=conversation)])
                response_text = response.content
            else:
                response_text = "I apologize, but the AI service is currently unavailable. Please try again later."

            # Add action context if available
            if state.get("last_action"):
                response_text = f"{state['last_action']}\n\n{response_text}"

            state["response"] = response_text

            # Update session state
            session_state.messages.append(HumanMessage(content=last_message))
            session_state.messages.append(AIMessage(content=response_text))

            return state

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["response"] = (
                "I apologize, but I'm having trouble processing your request right now. Could you please rephrase your question?"
            )
            return state

    async def _simple_response(self, message: str, state: AgentState) -> str:
        """Simple response generation without graph"""
        try:
            system_prompt = self._build_system_prompt(state)
            conversation = f"System: {system_prompt}\n\nUser: {message}\n\nAssistant:"

            if self.llm:
                response = await self.llm.ainvoke([HumanMessage(content=conversation)])
                return response.content
            else:
                return "Welcome to our hotel! I'm here to help you with your reservation needs. How can I assist you today?"

        except Exception as e:
            logger.error(f"Error in simple response: {e}")
            return "I'm here to help! What can I do for you today?"

    def _build_system_prompt(self, state: AgentState) -> str:
        """Build the system prompt based on current state"""
        base_prompt = """You are a professional hotel receptionist AI assistant at a luxury hotel. You are:
        - Friendly, warm, and welcoming
        - Professional and knowledgeable
        - Proactive in helping guests
        - Focused on creating exceptional experiences
        
        Your main goals:
        1. Help guests with room inquiries and bookings
        2. Collect guest information when needed
        3. Provide information about hotel amenities and services
        4. Make personalized recommendations
        5. Always end responses with engaging questions to continue the conversation
        
        Guidelines:
        - If you don't have guest information, politely ask for it
        - When showing rooms, mention specific features and benefits
        - Create urgency with phrases like "limited availability" or "popular choice"
        - Be conversational and use emojis appropriately
        - Always ask follow-up questions to keep the guest engaged"""

        # Add context based on current state
        if state.guest_info:
            guest_context = f"\nGuest Information Available:\n- Name: {state.guest_info.first_name} {state.guest_info.last_name}\n- Email: {state.guest_info.email}"
            base_prompt += guest_context
        else:
            base_prompt += "\nNote: No guest information available yet. Try to collect basic details (name, email, preferences)."

        if state.tools_used:
            tools_context = f"\nRecent actions taken: {', '.join(state.tools_used)}"
            base_prompt += tools_context

        if state.last_action:
            base_prompt += f"\nCurrent action: {state.last_action}"

        return base_prompt

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id not in self.sessions:
            return None

        state = self.sessions[session_id]
        return {
            "session_id": session_id,
            "guest_info": state.guest_info.model_dump() if state.guest_info else None,
            "message_count": len(state.messages),
            "tools_used": state.tools_used,
            "context": state.conversation_context,
        }

    def list_active_sessions(self) -> List[str]:
        """List all active session IDs"""
        return list(self.sessions.keys())


# ===== SINGLETON INSTANCE =====
hotel_agent = HotelAgent()
