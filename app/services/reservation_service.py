from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.guest_repository import GuestRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.reservation import (
    ReservationCreate, 
    ReservationUpdate, 
    ReservationResponse, 
    ReservationList,
    ReservationWithDetails
)
from app.models.reservation import Reservation, ReservationStatus
from app.models.room import RoomStatus


class ReservationService:
    def __init__(self):
        self.reservation_repo = ReservationRepository()
        self.guest_repo = GuestRepository()
        self.room_repo = RoomRepository()

    async def create_reservation(
        self, 
        db: AsyncSession, 
        reservation_data: ReservationCreate
    ) -> ReservationResponse:
        """Create a new reservation with validation"""
        # Validate guest exists
        guest = await self.guest_repo.get(db, reservation_data.guest_id)
        if not guest:
            raise HTTPException(
                status_code=404,
                detail="Guest not found"
            )
        
        # Validate room exists
        room = await self.room_repo.get(db, reservation_data.room_id)
        if not room:
            raise HTTPException(
                status_code=404,
                detail="Room not found"
            )
        
        # Check if room is available
        if room.status != RoomStatus.AVAILABLE:
            raise HTTPException(
                status_code=400,
                detail="Room is not available for reservation"
            )
        
        # Check for date conflicts
        conflicts = await self.reservation_repo.get_conflicting_reservations(
            db, 
            reservation_data.room_id,
            reservation_data.check_in_date,
            reservation_data.check_out_date
        )
        if conflicts:
            raise HTTPException(
                status_code=400,
                detail="Room is not available for the selected dates"
            )
        
        # Validate dates
        if reservation_data.check_in_date >= reservation_data.check_out_date:
            raise HTTPException(
                status_code=400,
                detail="Check-out date must be after check-in date"
            )
        
        # Generate reservation number
        reservation_number = await self.reservation_repo.generate_reservation_number(db)
        
        # Create reservation with generated number
        reservation_data_dict = reservation_data.model_dump()
        reservation_data_dict["reservation_number"] = reservation_number
        
        # Create the reservation
        reservation = await self.reservation_repo.create(db, reservation_data)
        
        # Update room status to reserved
        await self.room_repo.update_room_status(db, reservation_data.room_id, RoomStatus.RESERVED)
        
        return ReservationResponse.model_validate(reservation)

    async def get_reservation(
        self, 
        db: AsyncSession, 
        reservation_id: int
    ) -> ReservationResponse:
        """Get a reservation by ID"""
        reservation = await self.reservation_repo.get(db, reservation_id)
        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )
        return ReservationResponse.model_validate(reservation)

    async def get_reservations(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        guest_id: Optional[int] = None,
        room_id: Optional[int] = None,
        status: Optional[ReservationStatus] = None
    ) -> ReservationList:
        """Get reservations with optional filters"""
        if guest_id:
            reservations = await self.reservation_repo.get_by_guest(db, guest_id, skip, limit)
        elif room_id:
            reservations = await self.reservation_repo.get_by_room(db, room_id, skip, limit)
        else:
            filters = {}
            if status:
                filters["status"] = status
            reservations = await self.reservation_repo.get_multi(db, skip, limit, **filters)
        
        # Convert to detailed response
        detailed_reservations = []
        for reservation in reservations:
            guest = await self.guest_repo.get(db, reservation.guest_id)
            room = await self.room_repo.get(db, reservation.room_id)
            
            detailed_reservation = ReservationWithDetails(
                **reservation.__dict__,
                guest_name=f"{guest.first_name} {guest.last_name}",
                room_number=room.room_number,
                room_type=room.room_type.value
            )
            detailed_reservations.append(detailed_reservation)
        
        total = await self.reservation_repo.count(db)
        
        return ReservationList(
            reservations=detailed_reservations,
            total=total,
            page=skip // limit + 1,
            size=limit
        )

    async def update_reservation(
        self, 
        db: AsyncSession, 
        reservation_id: int, 
        reservation_data: ReservationUpdate
    ) -> ReservationResponse:
        """Update a reservation"""
        # Check if reservation exists
        existing_reservation = await self.reservation_repo.get(db, reservation_id)
        if not existing_reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )
        
        # Validate guest if updating
        if reservation_data.guest_id:
            guest = await self.guest_repo.get(db, reservation_data.guest_id)
            if not guest:
                raise HTTPException(
                    status_code=404,
                    detail="Guest not found"
                )
        
        # Validate room if updating
        if reservation_data.room_id:
            room = await self.room_repo.get(db, reservation_data.room_id)
            if not room:
                raise HTTPException(
                    status_code=404,
                    detail="Room not found"
                )
        
        # Check for date conflicts if updating dates
        if reservation_data.check_in_date or reservation_data.check_out_date:
            check_in = reservation_data.check_in_date or existing_reservation.check_in_date
            check_out = reservation_data.check_out_date or existing_reservation.check_out_date
            room_id = reservation_data.room_id or existing_reservation.room_id
            
            conflicts = await self.reservation_repo.get_conflicting_reservations(
                db, room_id, check_in, check_out, reservation_id
            )
            if conflicts:
                raise HTTPException(
                    status_code=400,
                    detail="Room is not available for the selected dates"
                )
        
        # Update the reservation
        updated_reservation = await self.reservation_repo.update(db, reservation_id, reservation_data)
        if not updated_reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )
        
        return ReservationResponse.model_validate(updated_reservation)

    async def cancel_reservation(
        self, 
        db: AsyncSession, 
        reservation_id: int, 
        reason: str,
        cancelled_by: str
    ) -> ReservationResponse:
        """Cancel a reservation"""
        reservation = await self.reservation_repo.get(db, reservation_id)
        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )
        
        if reservation.status in [ReservationStatus.CANCELLED, ReservationStatus.CHECKED_OUT]:
            raise HTTPException(
                status_code=400,
                detail="Reservation cannot be cancelled"
            )
        
        # Update reservation status
        update_data = ReservationUpdate(
            status=ReservationStatus.CANCELLED,
            cancellation_reason=reason,
            cancelled_by=cancelled_by
        )
        
        updated_reservation = await self.reservation_repo.update(db, reservation_id, update_data)
        
        # Update room status back to available
        await self.room_repo.update_room_status(db, reservation.room_id, RoomStatus.AVAILABLE)
        
        return ReservationResponse.model_validate(updated_reservation)

    async def get_guest_reservations(
        self, 
        db: AsyncSession, 
        guest_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> ReservationList:
        """Get reservations for a specific guest"""
        reservations = await self.reservation_repo.get_by_guest(db, guest_id, skip, limit)
        
        # Convert to detailed response
        detailed_reservations = []
        for reservation in reservations:
            guest = await self.guest_repo.get(db, reservation.guest_id)
            room = await self.room_repo.get(db, reservation.room_id)
            
            detailed_reservation = ReservationWithDetails(
                **reservation.__dict__,
                guest_name=f"{guest.first_name} {guest.last_name}",
                room_number=room.room_number,
                room_type=room.room_type.value
            )
            detailed_reservations.append(detailed_reservation)
        
        total = len(reservations)
        
        return ReservationList(
            reservations=detailed_reservations,
            total=total,
            page=skip // limit + 1,
            size=limit
        ) 