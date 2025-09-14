from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.room_service import RoomService
from app.services.sse_service import sse_service
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomList
from app.models.room import RoomStatus

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/", response_model=RoomResponse, status_code=201)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create new room."""
    room_service = RoomService()
    room = await room_service.create_room(db, room_data)
    rooms = await room_service.get_rooms(db, 0, 1000)
    await sse_service.notify_rooms_updated(rooms.rooms)
    return room


@router.get("/", response_model=RoomList)
async def get_rooms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    floor: Optional[int] = Query(None, ge=1, description="Filter by floor"),
    status: Optional[RoomStatus] = Query(None, description="Filter by room status"),
    db: AsyncSession = Depends(get_async_db)
):
    """Retrieve rooms with optional filters and pagination."""
    room_service = RoomService()
    return await room_service.get_rooms(db, skip, limit, room_type, floor, status)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get room by ID."""
    room_service = RoomService()
    return await room_service.get_room(db, room_id)


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    room_data: RoomUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update room information."""
    room_service = RoomService()
    room = await room_service.update_room(db, room_id, room_data)
    rooms = await room_service.get_rooms(db, 0, 1000)
    await sse_service.notify_rooms_updated(rooms.rooms)
    return room


@router.delete("/{room_id}", status_code=204)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete room."""
    room_service = RoomService()
    await room_service.delete_room(db, room_id)
    rooms = await room_service.get_rooms(db, 0, 1000)
    await sse_service.notify_rooms_updated(rooms.rooms)
    return None


@router.get("/available", response_model=RoomList)
async def get_available_rooms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get available rooms only."""
    room_service = RoomService()
    return await room_service.get_available_rooms(db, skip, limit)


@router.patch("/{room_id}/status", response_model=RoomResponse)
async def update_room_status(
    room_id: int,
    status: RoomStatus,
    db: AsyncSession = Depends(get_async_db)
):
    """Update room status."""
    room_service = RoomService()
    room = await room_service.update_room_status(db, room_id, status)
    rooms = await room_service.get_rooms(db, 0, 1000)
    await sse_service.notify_rooms_updated(rooms.rooms)
    return room


@router.get("/sse", include_in_schema=True, tags=["SSE - Real-time Updates"])
async def subscribe_to_room_updates():
    """Subscribe to real-time room updates via SSE."""
    return await sse_service.subscribe_to_room_updates() 