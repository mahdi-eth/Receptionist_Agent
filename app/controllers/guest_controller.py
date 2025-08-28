from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db
from app.services.guest_service import GuestService
from app.services.sse_service import sse_service
from app.schemas.guest import GuestCreate, GuestUpdate, GuestResponse, GuestList

router = APIRouter(prefix="/guests", tags=["guests"])


@router.post("/", response_model=GuestResponse, status_code=201)
async def create_guest(
    guest_data: GuestCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new guest"""
    guest_service = GuestService()
    guest = await guest_service.create_guest(db, guest_data)
    
    # Notify SSE subscribers
    await sse_service.notify_guest_created(guest)
    
    return guest


@router.get("/", response_model=GuestList)
async def get_guests(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for name or email"),
    db: AsyncSession = Depends(get_async_db)
):
    """Get guests with optional search and pagination"""
    guest_service = GuestService()
    return await guest_service.get_guests(db, skip, limit, search)


@router.get("/{guest_id}", response_model=GuestResponse)
async def get_guest(
    guest_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific guest by ID"""
    guest_service = GuestService()
    return await guest_service.get_guest(db, guest_id)


@router.put("/{guest_id}", response_model=GuestResponse)
async def update_guest(
    guest_id: int,
    guest_data: GuestUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update a guest"""
    guest_service = GuestService()
    guest = await guest_service.update_guest(db, guest_id, guest_data)
    
    # Notify SSE subscribers
    await sse_service.notify_guest_updated(guest)
    
    return guest


@router.delete("/{guest_id}", status_code=204)
async def delete_guest(
    guest_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete a guest (soft delete)"""
    guest_service = GuestService()
    await guest_service.delete_guest(db, guest_id)
    return None


@router.get("/search", response_model=GuestList)
async def search_guests(
    q: str = Query(..., description="Search term for name or email"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_async_db)
):
    """Search guests by name or email"""
    guest_service = GuestService()
    return await guest_service.search_guests(db, q, skip, limit)


@router.get("/sse/updates", include_in_schema=True, tags=["SSE - Real-time Updates"])
async def subscribe_to_guest_updates():
    """
    Subscribe to real-time guest updates via Server-Sent Events
    
    This endpoint establishes a Server-Sent Events connection that will send real-time updates
    whenever guests are created, updated, or deleted.
    
    Returns:
        EventSourceResponse: A streaming response with real-time guest updates
    """
    return await sse_service.subscribe_to_guests()