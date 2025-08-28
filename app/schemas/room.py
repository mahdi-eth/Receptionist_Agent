from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.room import RoomStatus, RoomType


class RoomBase(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=10)
    room_type: RoomType
    floor: int = Field(..., ge=1)
    capacity: int = Field(..., ge=1)
    price_per_night: float = Field(..., gt=0)
    description: Optional[str] = None
    amenities: Optional[str] = None
    notes: Optional[str] = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    room_number: Optional[str] = Field(None, min_length=1, max_length=10)
    room_type: Optional[RoomType] = None
    status: Optional[RoomStatus] = None
    floor: Optional[int] = Field(None, ge=1)
    capacity: Optional[int] = Field(None, ge=1)
    price_per_night: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    amenities: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class RoomResponse(RoomBase):
    id: int
    status: RoomStatus
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RoomList(BaseModel):
    rooms: list[RoomResponse]
    total: int
    page: int
    size: int 