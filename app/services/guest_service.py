from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.repositories.guest_repository import GuestRepository
from app.schemas.guest import GuestCreate, GuestUpdate, GuestResponse, GuestList
from app.models.guest import Guest


class GuestService:
    def __init__(self):
        self.repository = GuestRepository()

    async def create_guest(
        self, 
        db: AsyncSession, 
        guest_data: GuestCreate
    ) -> GuestResponse:
        """Create a new guest with validation"""
        # Check if email already exists
        existing_guest = await self.repository.get_by_email(db, guest_data.email)
        if existing_guest:
            raise HTTPException(
                status_code=400,
                detail="A guest with this email already exists"
            )
        
        # Create the guest
        guest = await self.repository.create(db, guest_data)
        return GuestResponse.model_validate(guest)

    async def get_guest(self, db: AsyncSession, guest_id: int) -> GuestResponse:
        """Get a guest by ID"""
        guest = await self.repository.get(db, guest_id)
        if not guest:
            raise HTTPException(
                status_code=404,
                detail="Guest not found"
            )
        return GuestResponse.model_validate(guest)

    async def get_guests(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ) -> GuestList:
        """Get guests with optional search"""
        if search:
            guests = await self.repository.search_guests(db, search, skip, limit)
        else:
            guests = await self.repository.get_multi(db, skip, limit)
        
        total = await self.repository.count(db)
        
        return GuestList(
            guests=[GuestResponse.model_validate(guest) for guest in guests],
            total=total,
            page=skip // limit + 1,
            size=limit
        )

    async def update_guest(
        self, 
        db: AsyncSession, 
        guest_id: int, 
        guest_data: GuestUpdate
    ) -> GuestResponse:
        """Update a guest"""
        # Check if guest exists
        existing_guest = await self.repository.get(db, guest_id)
        if not existing_guest:
            raise HTTPException(
                status_code=404,
                detail="Guest not found"
            )
        
        # Check email uniqueness if updating email
        if guest_data.email and guest_data.email != existing_guest.email:
            email_exists = await self.repository.get_by_email(db, guest_data.email)
            if email_exists:
                raise HTTPException(
                    status_code=400,
                    detail="A guest with this email already exists"
                )
        
        # Update the guest
        updated_guest = await self.repository.update(db, guest_id, guest_data)
        if not updated_guest:
            raise HTTPException(
                status_code=404,
                detail="Guest not found"
            )
        
        return GuestResponse.model_validate(updated_guest)

    async def delete_guest(self, db: AsyncSession, guest_id: int) -> bool:
        """Delete a guest (soft delete by setting is_active to False)"""
        existing_guest = await self.repository.get(db, guest_id)
        if not existing_guest:
            raise HTTPException(
                status_code=404,
                detail="Guest not found"
            )
        
        # Soft delete
        update_data = GuestUpdate(is_active=False)
        await self.repository.update(db, guest_id, update_data)
        return True

    async def search_guests(
        self, 
        db: AsyncSession, 
        search_term: str,
        skip: int = 0, 
        limit: int = 100
    ) -> GuestList:
        """Search guests by name or email"""
        guests = await self.repository.search_guests(db, search_term, skip, limit)
        total = len(guests)  # For search, we get the actual count
        
        return GuestList(
            guests=[GuestResponse.model_validate(guest) for guest in guests],
            total=total,
            page=skip // limit + 1,
            size=limit
        ) 