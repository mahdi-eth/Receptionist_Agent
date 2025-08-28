from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from typing import Optional, Dict, Any


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=True)  # Can be null for anonymous chats
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default="active", nullable=False)  # active, ended, expired
    context = Column(JSON, nullable=True)  # Store chat context and preferences
    session_metadata = Column(JSON, nullable=True)  # Store additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    guest = relationship("Guest", backref="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}', guest_id={self.guest_id})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_type = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_metadata = Column(JSON, nullable=True)  # Store message metadata like tokens, model used, etc.
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, type='{self.message_type}')>" 