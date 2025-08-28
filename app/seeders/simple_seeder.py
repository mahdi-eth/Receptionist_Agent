import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.guest import Guest
from app.models.room import Room, RoomType, RoomStatus
from app.models.reservation import Reservation, ReservationStatus
from app.services.guest_service import GuestService
from app.services.room_service import RoomService
from app.services.reservation_service import ReservationService
from app.schemas.guest import GuestCreate
from app.schemas.room import RoomCreate
from app.schemas.reservation import ReservationCreate
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SimpleDatabaseSeeder:
    def __init__(self):
        self.guest_service = GuestService()
        self.room_service = RoomService()
        self.reservation_service = ReservationService()

    async def seed_rooms(self, db: AsyncSession):
        """Seed the database with sample rooms"""
        print("🌆 Seeding rooms...")
        
        room_data = [
            {
                "room_number": "101",
                "room_type": RoomType.SINGLE,
                "floor": 1,
                "capacity": 1,
                "price_per_night": 89.99,
                "description": "Cozy single room with city view",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom"
            },
            {
                "room_number": "102",
                "room_type": RoomType.SINGLE,
                "floor": 1,
                "capacity": 1,
                "price_per_night": 89.99,
                "description": "Single room with garden view",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom"
            },
            {
                "room_number": "201",
                "room_type": RoomType.DOUBLE,
                "floor": 2,
                "capacity": 2,
                "price_per_night": 129.99,
                "description": "Spacious double room with balcony",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom, Balcony, Mini Fridge"
            },
            {
                "room_number": "202",
                "room_type": RoomType.DOUBLE,
                "floor": 2,
                "capacity": 2,
                "price_per_night": 129.99,
                "description": "Double room with city skyline view",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom, City View"
            },
            {
                "room_number": "301",
                "room_type": RoomType.SUITE,
                "floor": 3,
                "capacity": 4,
                "price_per_night": 249.99,
                "description": "Luxury suite with separate living area",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom, Living Room, Kitchenette, Balcony, Premium Toiletries"
            },
            {
                "room_number": "302",
                "room_type": RoomType.DELUXE,
                "floor": 3,
                "capacity": 3,
                "price_per_night": 189.99,
                "description": "Deluxe room with premium amenities",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom, Premium Bedding, Mini Bar, Work Desk"
            },
            {
                "room_number": "401",
                "room_type": RoomType.TRIPLE,
                "floor": 4,
                "capacity": 3,
                "price_per_night": 159.99,
                "description": "Triple room perfect for families",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom, Family-friendly"
            },
            {
                "room_number": "501",
                "room_type": RoomType.SUITE,
                "floor": 5,
                "capacity": 6,
                "price_per_night": 349.99,
                "description": "Presidential suite with panoramic views",
                "amenities": "WiFi, TV, Air Conditioning, Private Bathroom, Living Room, Dining Area, Kitchen, Jacuzzi, Panoramic Views, Butler Service"
            }
        ]
        
        created_rooms = []
        for room_info in room_data:
            try:
                room = await self.room_service.create_room(db, room_info)
                created_rooms.append(room)
                print(f"✅ Created room {room.room_number}")
            except Exception as e:
                print(f"⚠️ Room {room_info['room_number']} already exists: {e}")
        
        print(f"🏨 Created {len(created_rooms)} rooms")
        return created_rooms

    async def seed_guests(self, db: AsyncSession):
        """Seed the database with sample guests"""
        print("👥 Seeding guests...")
        
        guest_data = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0101",
                "address": "123 Main Street",
                "city": "New York",
                "country": "USA",
                "postal_code": "10001",
                "nationality": "American",
                "passport_number": "US123456789"
            },
            {
                "first_name": "Maria",
                "last_name": "Garcia",
                "email": "maria.garcia@email.com",
                "phone": "+34-555-0102",
                "address": "456 Calle Mayor",
                "city": "Madrid",
                "country": "Spain",
                "postal_code": "28001",
                "nationality": "Spanish",
                "passport_number": "ES987654321"
            },
            {
                "first_name": "David",
                "last_name": "Johnson",
                "email": "david.johnson@email.com",
                "phone": "+1-555-0103",
                "address": "789 Oak Avenue",
                "city": "Los Angeles",
                "country": "USA",
                "postal_code": "90210",
                "nationality": "American",
                "passport_number": "US987654321"
            },
            {
                "first_name": "Sophie",
                "last_name": "Martin",
                "email": "sophie.martin@email.com",
                "phone": "+33-555-0104",
                "address": "321 Rue de la Paix",
                "city": "Paris",
                "country": "France",
                "postal_code": "75001",
                "nationality": "French",
                "passport_number": "FR456789123"
            },
            {
                "first_name": "Ahmed",
                "last_name": "Hassan",
                "email": "ahmed.hassan@email.com",
                "phone": "+971-555-0105",
                "address": "654 Sheikh Zayed Road",
                "city": "Dubai",
                "country": "UAE",
                "postal_code": "00000",
                "nationality": "Emirati",
                "passport_number": "AE123789456"
            }
        ]
        
        created_guests = []
        for guest_info in guest_data:
            try:
                guest = await self.guest_service.create_guest(db, guest_info)
                created_guests.append(guest)
                print(f"✅ Created guest {guest.first_name} {guest.last_name}")
            except Exception as e:
                print(f"⚠️ Guest {guest_info['email']} already exists: {e}")
        
        print(f"👥 Created {len(created_guests)} guests")
        return created_guests

    async def seed_reservations(self, db: AsyncSession, rooms, guests):
        """Seed the database with sample reservations"""
        print("📅 Seeding reservations...")
        
        # Create some past, current, and future reservations
        base_date = datetime.now()
        
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
                print(f"✅ Created reservation {reservation.reservation_number}")
            except Exception as e:
                print(f"⚠️ Failed to create reservation: {e}")
        
        print(f"📅 Created {len(created_reservations)} reservations")
        return created_reservations

    async def seed_database(self):
        """Seed the entire database with sample data"""
        print("🌱 Starting database seeding...")
        
        async with AsyncSessionLocal() as db:
            try:
                # Seed rooms first
                rooms = await self.seed_rooms(db)
                
                # Only seed guests and reservations if we have rooms
                if rooms:
                    # Seed guests
                    guests = await self.seed_guests(db)
                    
                    # Only seed reservations if we have both rooms and guests
                    if guests:
                        reservations = await self.seed_reservations(db, rooms, guests)
                    else:
                        reservations = []
                        print("⚠️ Skipping reservations - no guests created")
                else:
                    guests = []
                    reservations = []
                    print("⚠️ Skipping guests and reservations - no rooms created")
                
                print("🎉 Database seeding completed successfully!")
                print(f"📊 Summary:")
                print(f"   🏨 Rooms: {len(rooms)}")
                print(f"   👥 Guests: {len(guests)}")
                print(f"   📅 Reservations: {len(reservations)}")
                
                if not rooms and not guests:
                    print("\n💡 Note: It appears the database already contains sample data.")
                    print("   The seeder skipped creating duplicate entries.")
                    print("   You can now start the application with: python start.py")
                
            except Exception as e:
                print(f"❌ Database seeding failed: {e}")
                raise


async def main():
    """Main function to run the seeder"""
    seeder = SimpleDatabaseSeeder()
    await seeder.seed_database()


if __name__ == "__main__":
    asyncio.run(main()) 