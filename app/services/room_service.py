from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.repositories.room_repository import RoomRepository
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse, RoomList
from app.models.room import Room, RoomStatus, RoomType


class RoomService:
    def __init__(self):
        self.repository = RoomRepository()

    async def create_room(
        self, 
        db: AsyncSession, 
        room_data: RoomCreate
    ) -> RoomResponse:
        """Create a new room with validation"""
        # Check if room number already exists
        existing_room = await self.repository.get_by_room_number(db, room_data.room_number)
        if existing_room:
            raise HTTPException(
                status_code=400,
                detail="A room with this number already exists"
            )
        
        # Create the room
        room = await self.repository.create(db, room_data)
        return RoomResponse.model_validate(room)

    async def get_room(self, db: AsyncSession, room_id: int) -> RoomResponse:
        """Get a room by ID"""
        room = await self.repository.get(db, room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )
        return RoomResponse.model_validate(room)

    async def get_rooms(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        room_type: Optional[str] = None,
        floor: Optional[int] = None,
        status: Optional[RoomStatus] = None
    ) -> RoomList:
        """Get rooms with optional filters"""
        filters = {}
        if room_type:
            filters["room_type"] = room_type
        if floor:
            filters["floor"] = floor
        if status:
            filters["status"] = status
        
        rooms = await self.repository.get_multi(db, skip, limit, **filters)
        total = await self.repository.count(db, **filters)
        
        return RoomList(
            rooms=[RoomResponse.model_validate(room) for room in rooms],
            total=total,
            page=skip // limit + 1,
            size=limit
        )

    async def update_room(
        self, 
        db: AsyncSession, 
        room_id: int, 
        room_data: RoomUpdate
    ) -> RoomResponse:
        """Update a room"""
        # Check if room exists
        existing_room = await self.repository.get(db, room_id)
        if not existing_room:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )
        
        # Check room number uniqueness if updating room number
        if room_data.room_number and room_data.room_number != existing_room.room_number:
            room_number_exists = await self.repository.get_by_room_number(db, room_data.room_number)
            if room_number_exists:
                raise HTTPException(
                    status_code=400,
                    detail="A room with this number already exists"
                )
        
        # Update the room
        updated_room = await self.repository.update(db, room_id, room_data)
        if not updated_room:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )
        
        return RoomResponse.model_validate(updated_room)

    async def delete_room(self, db: AsyncSession, room_id: int) -> bool:
        """Delete a room (soft delete by setting is_active to False)"""
        existing_room = await self.repository.get(db, room_id)
        if not existing_room:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )
        
        # Soft delete
        update_data = RoomUpdate(is_active=False)
        await self.repository.update(db, room_id, update_data)
        return True

    async def get_available_rooms(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> RoomList:
        """Get only available rooms"""
        rooms = await self.repository.get_available_rooms(db, skip, limit)
        total = await self.repository.count(db, status=RoomStatus.AVAILABLE)
        
        return RoomList(
            rooms=[RoomResponse.model_validate(room) for room in rooms],
            total=total,
            page=skip // limit + 1,
            size=limit
        )

    async def update_room_status(
        self, 
        db: AsyncSession, 
        room_id: int, 
        status: RoomStatus
    ) -> RoomResponse:
        """Update room status"""
        room = await self.repository.update_room_status(db, room_id, status)
        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )
        return RoomResponse.model_validate(room) 