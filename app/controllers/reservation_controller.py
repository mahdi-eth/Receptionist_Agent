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
    """Create new reservation."""
    reservation_service = ReservationService()
    reservation = await reservation_service.create_reservation(db, reservation_data)
    await sse_service.notify_reservation_created(reservation, reservation.guest_id)
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
    """Retrieve reservations with optional filters and pagination."""
    reservation_service = ReservationService()
    return await reservation_service.get_reservations(db, skip, limit, guest_id, room_id, status)


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get reservation by ID."""
    reservation_service = ReservationService()
    return await reservation_service.get_reservation(db, reservation_id)


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    reservation_data: ReservationUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update reservation information."""
    reservation_service = ReservationService()
    reservation = await reservation_service.update_reservation(db, reservation_id, reservation_data)
    await sse_service.notify_reservation_updated(reservation, reservation.guest_id)
    return reservation


@router.delete("/{reservation_id}", status_code=204)
async def delete_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete reservation."""
    reservation_service = ReservationService()
    reservation = await reservation_service.get_reservation(db, reservation_id)
    update_data = ReservationUpdate(is_active=False)
    await reservation_service.update_reservation(db, reservation_id, update_data)
    await sse_service.notify_reservation_updated(reservation, reservation.guest_id)
    return None


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation(
    reservation_id: int,
    reason: str = Query(..., description="Reason for cancellation"),
    cancelled_by: str = Query(..., description="Who cancelled the reservation"),
    db: AsyncSession = Depends(get_async_db)
):
    """Cancel reservation."""
    reservation_service = ReservationService()
    reservation = await reservation_service.cancel_reservation(db, reservation_id, reason, cancelled_by)
    await sse_service.notify_reservation_cancelled(reservation, reservation.guest_id)
    return reservation


@router.get("/guest/{guest_id}", response_model=ReservationList)
async def get_guest_reservations(
    guest_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get reservations for specific guest."""
    reservation_service = ReservationService()
    return await reservation_service.get_guest_reservations(db, guest_id, skip, limit)


@router.get("/guest/{guest_id}/sse", include_in_schema=True, tags=["SSE - Real-time Updates"])
async def subscribe_to_guest_reservation_updates(guest_id: int):
    """Subscribe to real-time reservation updates for guest via SSE."""
    return await sse_service.subscribe_to_reservation_updates(guest_id)