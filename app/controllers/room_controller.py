from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.room_service import RoomService
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomList
from app.models.room import RoomStatus

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("/", response_model=RoomResponse, status_code=201)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new room"""
    room_service = RoomService()
    return await room_service.create_room(db, room_data)


@router.get("/", response_model=RoomList)
async def get_rooms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    room_type: Optional[str] = Query(None, description="Filter by room type"),
    floor: Optional[int] = Query(None, ge=1, description="Filter by floor"),
    status: Optional[RoomStatus] = Query(None, description="Filter by room status"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get rooms with optional filters and pagination"""
    room_service = RoomService()
    return await room_service.get_rooms(db, skip, limit, room_type, floor, status)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific room by ID"""
    room_service = RoomService()
    return await room_service.get_room(db, room_id)


@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: int,
    room_data: RoomUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a room"""
    room_service = RoomService()
    return await room_service.update_room(db, room_id, room_data)


@router.delete("/{room_id}", status_code=204)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a room (soft delete)"""
    room_service = RoomService()
    await room_service.delete_room(db, room_id)
    return None


@router.get("/available", response_model=RoomList)
async def get_available_rooms(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get only available rooms"""
    room_service = RoomService()
    return await room_service.get_available_rooms(db, skip, limit)


@router.patch("/{room_id}/status", response_model=RoomResponse)
async def update_room_status(
    room_id: int,
    status: RoomStatus,
    db: AsyncSession = Depends(get_async_db)
):
    """Update room status"""
    room_service = RoomService()
    return await room_service.update_room_status(db, room_id, status)


@router.get("/sse/status-updates", include_in_schema=True, tags=["SSE - Real-time Updates"])
async def subscribe_to_room_status_updates():
    """
    Subscribe to real-time room status updates via Server-Sent Events
    
    This endpoint establishes a Server-Sent Events connection that will send real-time updates
    whenever room statuses change (available, occupied, maintenance, etc.).
    
    Returns:
        EventSourceResponse: A streaming response with real-time room status updates
    """
    from app.services.sse_service import sse_service
    # For now, return a simple message - you can enhance this later
    from fastapi.responses import StreamingResponse
    import json
    
    async def event_stream():
        yield f"data: {json.dumps({'message': 'Room status updates stream started'})}\n\n"
        while True:
            import asyncio
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            yield f"data: {json.dumps({'timestamp': '2024-01-01T00:00:00Z', 'type': 'heartbeat'})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    ) 