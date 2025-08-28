from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.reservation_service import ReservationService
from app.services.sse_service import sse_service
from app.schemas.reservation import (
    ReservationCreate, 
    ReservationUpdate, 
    ReservationResponse, 
    ReservationList
)
from app.models.reservation import ReservationStatus

router = APIRouter(prefix="/reservations", tags=["reservations"])


@router.post("/", response_model=ReservationResponse, status_code=201)
async def create_reservation(
    reservation_data: ReservationCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new reservation"""
    reservation_service = ReservationService()
    reservation = await reservation_service.create_reservation(db, reservation_data)
    
    # Notify SSE subscribers about the new reservation
    # We need to get the detailed reservation for notification
    detailed_reservation = await reservation_service.get_reservation(db, reservation.id)
    await sse_service.notify_reservation_created(detailed_reservation)
    
    return reservation


@router.get("/", response_model=ReservationList)
async def get_reservations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    guest_id: Optional[int] = Query(None, description="Filter by guest ID"),
    room_id: Optional[int] = Query(None, description="Filter by room ID"),
    status: Optional[ReservationStatus] = Query(None, description="Filter by reservation status"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get reservations with optional filters and pagination"""
    reservation_service = ReservationService()
    return await reservation_service.get_reservations(db, skip, limit, guest_id, room_id, status)


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific reservation by ID"""
    reservation_service = ReservationService()
    return await reservation_service.get_reservation(db, reservation_id)


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    reservation_data: ReservationUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a reservation"""
    reservation_service = ReservationService()
    reservation = await reservation_service.update_reservation(db, reservation_id, reservation_data)
    
    # Notify SSE subscribers about the updated reservation
    detailed_reservation = await reservation_service.get_reservation(db, reservation.id)
    await sse_service.notify_reservation_updated(detailed_reservation)
    
    return reservation


@router.delete("/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a reservation (soft delete)"""
    reservation_service = ReservationService()
    # For now, we'll use the update method to set is_active to False
    # You might want to implement a proper delete method in the service
    update_data = ReservationUpdate(is_active=False)
    await reservation_service.update_reservation(db, reservation_id, update_data)
    return None


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation(
    reservation_id: int,
    reason: str = Query(..., description="Reason for cancellation"),
    cancelled_by: str = Query(..., description="Who cancelled the reservation"),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel a reservation"""
    reservation_service = ReservationService()
    reservation = await reservation_service.cancel_reservation(db, reservation_id, reason, cancelled_by)
    
    # Notify SSE subscribers about the cancelled reservation
    detailed_reservation = await reservation_service.get_reservation(db, reservation.id)
    await sse_service.notify_reservation_cancelled(detailed_reservation)
    
    return reservation


@router.get("/guest/{guest_id}", response_model=ReservationList)
async def get_guest_reservations(
    guest_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get reservations for a specific guest"""
    reservation_service = ReservationService()
    return await reservation_service.get_guest_reservations(db, guest_id, skip, limit)


@router.get("/guest/{guest_id}/sse/updates", include_in_schema=True, tags=["SSE - Real-time Updates"])
async def subscribe_to_guest_reservation_updates(guest_id: int):
    """
    Subscribe to real-time reservation updates for a specific guest via Server-Sent Events
    
    This endpoint establishes a Server-Sent Events connection that will send real-time updates
    whenever reservations for the specified guest are created, updated, or cancelled.
    
    Args:
        guest_id (int): The ID of the guest to subscribe to reservation updates for
        
    Returns:
        EventSourceResponse: A streaming response with real-time reservation updates
    """
    return await sse_service.subscribe_to_reservations(guest_id)