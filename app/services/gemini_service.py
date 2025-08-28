import google.generativeai as genai
import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        try:
            self.api_key = getattr(settings, 'gemini_api_key', None)
            if not self.api_key or self.api_key == "":
                logger.warning("GEMINI_API_KEY not configured")
                self.api_key = None
                self.model = None
                return
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Gemini service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            self.api_key = None
            self.model = None

    async def generate_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response using Gemini AI"""
        try:
            # If Gemini is not available, raise error
            if not self.model:
                raise ValueError("Gemini service not available")
            
            # Prepare the conversation context for Gemini 2.0
            # Gemini 2.0 doesn't support system role, so we'll include context in the first user message
            messages = []
            
            # Create initial context message
            context_message = "You are a professional hotel receptionist at a luxury hotel. You are friendly, helpful, and knowledgeable about hotel services. Your role is to help guests with inquiries about rooms, amenities, and services, assist with room bookings and reservations, handle guest registration and check-in/check-out processes, provide information about local attractions and services, and address guest concerns and requests professionally. Always maintain a warm, welcoming tone while being professional and efficient."
            
            if context:
                context_message += f"\n\nContext: {json.dumps(context, indent=2)}"
            
            # Add context as first user message
            messages.append({
                "role": "user",
                "parts": [context_message]
            })
            
            # Add conversation history (skip system messages)
            for msg in conversation_history:
                if msg["role"] != "system":  # Skip system messages
                    messages.append({
                        "role": msg["role"],
                        "parts": [msg["content"]]
                    })
            
            # Add current user message
            messages.append({
                "role": "user",
                "parts": [user_message]
            })
            
            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                messages
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            raise e

    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """Analyze user intent from message"""
        try:
            if not self.model:
                raise ValueError("Gemini service not available")
            
            analysis_prompt = f"""
            Analyze the following hotel guest message and extract the intent and required information:
            
            Message: "{message}"
            
            Please respond with a JSON object containing:
            {{
                "intent": "booking|inquiry|check_in|check_out|complaint|general",
                "entities": {{
                    "room_type": "single|double|suite|deluxe|triple",
                    "dates": "check_in and check_out dates if mentioned",
                    "guests": "number of guests if mentioned",
                    "budget": "price range if mentioned",
                    "amenities": "specific amenities requested"
                }},
                "urgency": "low|medium|high",
                "requires_action": true/false
            }}
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                analysis_prompt
            )
            
            # Try to parse JSON response
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                # Return basic intent if JSON parsing fails
                return {
                    "intent": "general",
                    "entities": {},
                    "urgency": "low",
                    "requires_action": False
                }
                
        except Exception as e:
            logger.error(f"Error analyzing intent: {e}")
            raise e

    async def generate_tool_calls(
        self, 
        message: str, 
        available_tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate tool calls based on user message"""
        try:
            if not self.model:
                raise ValueError("Gemini service not available")
            
            tools_prompt = f"""
            Based on the user message, determine which tools should be called and with what parameters.
            
            User message: "{message}"
            
            Available tools: {json.dumps(available_tools, indent=2)}
            
            Respond with a JSON array of tool calls:
            [
                {{
                    "tool": "tool_name",
                    "parameters": {{
                        "param1": "value1",
                        "param2": "value2"
                    }},
                    "reasoning": "Why this tool is needed"
                }}
            ]
            
            Only include tools that are actually needed based on the user's request.
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                tools_prompt
            )
            
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            logger.error(f"Error generating tool calls: {e}")
            raise e

    async def format_response_with_context(
        self, 
        response: str, 
        context: Dict[str, Any]
    ) -> str:
        """Format response with additional context"""
        try:
            if not self.model:
                raise ValueError("Gemini service not available")
            
            context_prompt = f"""
            Format the following response to include relevant context information:
            
            Response: "{response}"
            
            Context: {json.dumps(context, indent=2)}
            
            Enhance the response with relevant context while maintaining natural flow.
            """
            
            enhanced_response = await asyncio.to_thread(
                self.model.generate_content,
                context_prompt
            )
            
            return enhanced_response.text
            
        except Exception as e:
            logger.error(f"Error formatting response with context: {e}")
            raise e 