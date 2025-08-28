from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, Enum, DateTime
from sqlalchemy.sql import func
import enum
from app.database import Base


class RoomStatus(enum.Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    CLEANING = "cleaning"
    RESERVED = "reserved"


class RoomType(enum.Enum):
    SINGLE = "single"
    DOUBLE = "double"
    TRIPLE = "triple"
    SUITE = "suite"
    DELUXE = "deluxe"


class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(10), unique=True, nullable=False, index=True)
    room_type = Column(Enum(RoomType), nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE, nullable=False)
    floor = Column(Integer, nullable=False)
    capacity = Column(Integer, nullable=False)
    price_per_night = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)  # JSON string or comma-separated
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Room(id={self.id}, number='{self.room_number}', type='{self.room_type.value}', status='{self.status.value}')>" 