from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.reservation import ReservationStatus


class ReservationBase(BaseModel):
    guest_id: int = Field(..., gt=0)
    room_id: int = Field(..., gt=0)
    check_in_date: datetime
    check_out_date: datetime
    total_amount: float = Field(..., gt=0)
    deposit_amount: Optional[float] = Field(None, ge=0)
    special_requests: Optional[str] = None
    notes: Optional[str] = None


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(BaseModel):
    guest_id: Optional[int] = Field(None, gt=0)
    room_id: Optional[int] = Field(None, gt=0)
    check_in_date: Optional[datetime] = None
    check_out_date: Optional[datetime] = None
    status: Optional[ReservationStatus] = None
    total_amount: Optional[float] = Field(None, gt=0)
    deposit_amount: Optional[float] = Field(None, ge=0)
    special_requests: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ReservationResponse(ReservationBase):
    id: int
    reservation_number: str
    status: ReservationStatus
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReservationWithDetails(ReservationResponse):
    guest_name: str
    room_number: str
    room_type: str


class ReservationList(BaseModel):
    reservations: list[ReservationWithDetails]
    total: int
    page: int
    size: int 