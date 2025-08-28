import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.services.room_service import RoomService
from app.services.guest_service import GuestService
from app.services.reservation_service import ReservationService
from app.schemas.room import RoomCreate
from app.schemas.guest import GuestCreate
from app.schemas.reservation import ReservationCreate
from app.models.room import RoomType, RoomStatus
from app.models.reservation import ReservationStatus


class DatabaseSeeder:
    """Database seeder for initial data"""
    
    def __init__(self):
        self.room_service = RoomService()
        self.guest_service = GuestService()
        self.reservation_service = ReservationService()

    async def seed_rooms(self, db: AsyncSession):
        """Seed rooms with sample data"""
        room_data = [
            {
                "room_number": "101",
                "room_type": RoomType.SINGLE,
                "floor": 1,
                "capacity": 1,
                "price_per_night": 89.99,
                "status": RoomStatus.AVAILABLE,
                "amenities": ["WiFi", "TV", "Air Conditioning", "Private Bathroom"]
            },
            {
                "room_number": "102",
                "room_type": RoomType.DOUBLE,
                "floor": 1,
                "capacity": 2,
                "price_per_night": 129.99,
                "status": RoomStatus.AVAILABLE,
                "amenities": ["WiFi", "TV", "Air Conditioning", "Private Bathroom", "Mini Fridge"]
            },
            {
                "room_number": "201",
                "room_type": RoomType.DOUBLE,
                "floor": 2,
                "capacity": 2,
                "price_per_night": 139.99,
                "status": RoomStatus.AVAILABLE,
                "amenities": ["WiFi", "TV", "Air Conditioning", "Private Bathroom", "Mini Fridge", "Balcony"]
            },
            {
                "room_number": "202",
                "room_type": RoomType.SUITE,
                "floor": 2,
                "capacity": 3,
                "price_per_night": 249.99,
                "status": RoomStatus.AVAILABLE,
                "amenities": ["WiFi", "TV", "Air Conditioning", "Private Bathroom", "Mini Fridge", "Balcony", "Living Room", "Kitchenette"]
            },
            {
                "room_number": "301",
                "room_type": RoomType.DELUXE,
                "floor": 3,
                "capacity": 2,
                "price_per_night": 189.99,
                "status": RoomStatus.AVAILABLE,
                "amenities": ["WiFi", "TV", "Air Conditioning", "Private Bathroom", "Mini Fridge", "Balcony", "City View"]
            }
        ]
        
        created_rooms = []
        for room_info in room_data:
            try:
                room = await self.room_service.create_room(db, RoomCreate(**room_info))
                created_rooms.append(room)
            except Exception as e:
                # Try to get existing room
                try:
                    existing_room = await self.room_service.get_room_by_number(db, room_info["room_number"])
                    if existing_room:
                        created_rooms.append(existing_room)
                except Exception as ex:
                    pass
        
        return created_rooms

    async def seed_guests(self, db: AsyncSession):
        """Seed guests with sample data"""
        guest_data = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0101",
                "address": "123 Main St, Anytown, USA",
                "date_of_birth": datetime(1985, 3, 15),
                "nationality": "US",
                "id_type": "passport",
                "id_number": "US123456789"
            },
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah.johnson@email.com",
                "phone": "+1-555-0102",
                "address": "456 Oak Ave, Somewhere, USA",
                "date_of_birth": datetime(1990, 7, 22),
                "nationality": "US",
                "id_type": "driver_license",
                "id_number": "DL987654321"
            },
            {
                "first_name": "Michael",
                "last_name": "Brown",
                "email": "michael.brown@email.com",
                "phone": "+1-555-0103",
                "address": "789 Pine Rd, Elsewhere, USA",
                "date_of_birth": datetime(1978, 11, 8),
                "nationality": "US",
                "id_type": "passport",
                "id_number": "US987654321"
            },
            {
                "first_name": "Emily",
                "last_name": "Davis",
                "email": "emily.davis@email.com",
                "phone": "+1-555-0104",
                "address": "321 Elm St, Nowhere, USA",
                "date_of_birth": datetime(1992, 4, 12),
                "nationality": "US",
                "id_type": "driver_license",
                "id_number": "DL123456789"
            },
            {
                "first_name": "David",
                "last_name": "Wilson",
                "email": "david.wilson@email.com",
                "phone": "+1-555-0105",
                "address": "654 Maple Dr, Anywhere, USA",
                "date_of_birth": datetime(1983, 9, 30),
                "nationality": "US",
                "id_type": "passport",
                "id_number": "US456789123"
            }
        ]
        
        created_guests = []
        for guest_info in guest_data:
            try:
                guest = await self.guest_service.create_guest(db, GuestCreate(**guest_info))
                created_guests.append(guest)
            except Exception as e:
                # Try to get existing guest
                try:
                    existing_guest = await self.guest_service.get_guest_by_email(db, guest_info["email"])
                    if existing_guest:
                        created_guests.append(existing_guest)
                except Exception as ex:
                    pass
        
        return created_guests

    async def seed_reservations(self, db: AsyncSession, rooms, guests):
        """Seed reservations with sample data"""
        base_date = datetime.now().date()
        
        reservation_data = [
            {
                "guest_id": guests[0].id,
                "room_id": rooms[0].id,
                "check_in_date": base_date + timedelta(days=1),
                "check_out_date": base_date + timedelta(days=3),
                "total_amount": 179.98,
                "deposit_amount": 50.00,
                "special_requests": "Early check-in if possible"
            },
            {
                "guest_id": guests[1].id,
                "room_id": rooms[2].id,
                "check_in_date": base_date + timedelta(days=2),
                "check_out_date": base_date + timedelta(days=5),
                "total_amount": 389.97,
                "deposit_amount": 100.00,
                "special_requests": "Room with balcony preferred"
            },
            {
                "guest_id": guests[2].id,
                "room_id": rooms[4].id,
                "check_in_date": base_date + timedelta(days=7),
                "check_out_date": base_date + timedelta(days=10),
                "total_amount": 749.97,
                "deposit_amount": 200.00,
                "special_requests": "High floor room with city view"
            },
            {
                "guest_id": guests[3].id,
                "room_id": rooms[1].id,
                "check_in_date": base_date - timedelta(days=5),
                "check_out_date": base_date - timedelta(days=2),
                "total_amount": 269.97,
                "status": ReservationStatus.CHECKED_OUT
            },
            {
                "guest_id": guests[4].id,
                "room_id": rooms[3].id,
                "check_in_date": base_date - timedelta(days=10),
                "check_out_date": base_date - timedelta(days=7),
                "total_amount": 389.97,
                "status": ReservationStatus.CHECKED_OUT
            }
        ]
        
        created_reservations = []
        for reservation_info in reservation_data:
            try:
                reservation = await self.reservation_service.create_reservation(db, reservation_info)
                created_reservations.append(reservation)
            except Exception as e:
                pass
        
        return created_reservations

    async def seed_database(self):
        """Seed the entire database with sample data"""
        async with AsyncSessionLocal() as db:
            try:
                # Seed rooms first
                rooms = await self.seed_rooms(db)
                
                # Seed guests
                guests = await self.seed_guests(db)
                
                # Seed reservations
                reservations = await self.seed_reservations(db, rooms, guests)
                
            except Exception as e:
                raise


async def main():
    """Main function to run the seeder"""
    seeder = DatabaseSeeder()
    await seeder.seed_database()


if __name__ == "__main__":
    asyncio.run(main()) 