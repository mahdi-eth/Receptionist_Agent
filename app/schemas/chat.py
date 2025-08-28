from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatSessionBase(BaseModel):
    guest_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    session_metadata: Optional[Dict[str, Any]] = None


class ChatSessionCreate(ChatSessionBase):
    session_id: str = Field(..., min_length=1, max_length=50)


class ChatSessionUpdate(BaseModel):
    status: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    session_metadata: Optional[Dict[str, Any]] = None
    ended_at: Optional[datetime] = None


class ChatSessionResponse(ChatSessionBase):
    id: int
    session_id: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(user|assistant|system)$")
    message_type: str = Field(..., pattern="^(user|assistant|system)$")
    message_metadata: Optional[Dict[str, Any]] = None


class ChatMessageCreate(ChatMessageBase):
    session_id: int


class ChatMessageResponse(ChatMessageBase):
    id: int
    session_id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ChatSessionWithMessages(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's message")
    session_id: Optional[str] = None
    guest_id: Optional[int] = None


class ChatResponse(BaseModel):
    message: str
    session_id: str
    guest_id: Optional[int] = None
    timestamp: datetime


class ChatSessionEnd(BaseModel):
    session_id: str
    reason: Optional[str] = None 