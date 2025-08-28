from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.repositories.base_repository import BaseRepository
from app.models.guest import Guest
from app.schemas.guest import GuestCreate, GuestUpdate


class GuestRepository(BaseRepository[Guest, GuestCreate, GuestUpdate]):
    def __init__(self):
        super().__init__(Guest)

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[Guest]:
        """Get guest by email"""
        result = await db.execute(
            select(Guest).where(Guest.email == email)
        )
        return result.scalar_one_or_none()

    async def search_guests(
        self, 
        db: AsyncSession, 
        search_term: str,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Guest]:
        """Search guests by name or email"""
        query = select(Guest).where(
            or_(
                Guest.first_name.ilike(f"%{search_term}%"),
                Guest.last_name.ilike(f"%{search_term}%"),
                Guest.email.ilike(f"%{search_term}%")
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_guests(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Guest]:
        """Get only active guests"""
        return await self.get_multi(db, skip=skip, limit=limit, is_active=True)

    async def get_guests_with_reservations(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Guest]:
        """Get guests with their reservations loaded"""
        query = select(Guest).options(
            selectinload(Guest.reservations)
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all() 