from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from app.repositories.base_repository import BaseRepository
from app.models.room import Room, RoomStatus
from app.schemas.room import RoomCreate, RoomUpdate


class RoomRepository(BaseRepository[Room, RoomCreate, RoomUpdate]):
    def __init__(self):
        super().__init__(Room)

    async def get_by_room_number(self, db: AsyncSession, room_number: str) -> Optional[Room]:
        """Get room by room number"""
        result = await db.execute(
            select(Room).where(Room.room_number == room_number)
        )
        return result.scalar_one_or_none()

    async def get_available_rooms(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Room]:
        """Get only available rooms"""
        return await self.get_multi(db, skip=skip, limit=limit, status=RoomStatus.AVAILABLE)

    async def get_rooms_by_type(
        self, 
        db: AsyncSession, 
        room_type: str,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Room]:
        """Get rooms by type"""
        return await self.get_multi(db, skip=skip, limit=limit, room_type=room_type)

    async def get_rooms_by_floor(
        self, 
        db: AsyncSession, 
        floor: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Room]:
        """Get rooms by floor"""
        return await self.get_multi(db, skip=skip, limit=limit, floor=floor)

    async def update_room_status(
        self, 
        db: AsyncSession, 
        room_id: int, 
        status: RoomStatus
    ) -> Optional[Room]:
        """Update room status"""
        await db.execute(
            select(Room).where(Room.id == room_id)
        )
        room = await self.get(db, room_id)
        if room:
            room.status = status
            await db.commit()
            await db.refresh(room)
        return room 