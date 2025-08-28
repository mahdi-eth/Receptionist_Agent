from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime
from app.repositories.base_repository import BaseRepository
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.reservation import ReservationCreate, ReservationUpdate


class ReservationRepository(BaseRepository[Reservation, ReservationCreate, ReservationUpdate]):
    def __init__(self):
        super().__init__(Reservation)

    async def get_by_reservation_number(
        self, 
        db: AsyncSession, 
        reservation_number: str
    ) -> Optional[Reservation]:
        """Get reservation by reservation number"""
        result = await db.execute(
            select(Reservation).where(Reservation.reservation_number == reservation_number)
        )
        return result.scalar_one_or_none()

    async def get_by_guest(
        self, 
        db: AsyncSession, 
        guest_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Reservation]:
        """Get reservations by guest ID"""
        return await self.get_multi(db, skip=skip, limit=limit, guest_id=guest_id)

    async def get_by_room(
        self, 
        db: AsyncSession, 
        room_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Reservation]:
        """Get reservations by room ID"""
        return await self.get_multi(db, skip=skip, limit=limit, room_id=room_id)

    async def get_by_date_range(
        self, 
        db: AsyncSession, 
        start_date: datetime,
        end_date: datetime,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Reservation]:
        """Get reservations within a date range"""
        query = select(Reservation).where(
            and_(
                Reservation.check_in_date <= end_date,
                Reservation.check_out_date >= start_date
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_active_reservations(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Reservation]:
        """Get only active reservations"""
        active_statuses = [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECKED_IN
        ]
        
        query = select(Reservation).where(
            and_(
                Reservation.status.in_(active_statuses),
                Reservation.is_active == True
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_conflicting_reservations(
        self, 
        db: AsyncSession, 
        room_id: int,
        check_in_date: datetime,
        check_out_date: datetime,
        exclude_id: Optional[int] = None
    ) -> List[Reservation]:
        """Get reservations that conflict with given dates for a room"""
        query = select(Reservation).where(
            and_(
                Reservation.room_id == room_id,
                Reservation.is_active == True,
                Reservation.status.in_([
                    ReservationStatus.PENDING,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.CHECKED_IN
                ]),
                or_(
                    and_(
                        Reservation.check_in_date < check_out_date,
                        Reservation.check_out_date > check_in_date
                    )
                )
            )
        )
        
        if exclude_id:
            query = query.where(Reservation.id != exclude_id)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def generate_reservation_number(self, db: AsyncSession) -> str:
        """Generate a unique reservation number"""
        import uuid
        return f"RES-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}" 