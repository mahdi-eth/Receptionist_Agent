import asyncio
import json
from typing import Dict, Set, Any
from datetime import datetime
from sse_starlette.sse import EventSourceResponse
from app.schemas.guest import GuestResponse
from app.schemas.reservation import ReservationWithDetails


class SSEService:
    def __init__(self):
        self.guest_subscribers: Set[str] = set()
        self.reservation_subscribers: Dict[int, Set[str]] = {}  # guest_id -> set of subscriber_ids
        
    def generate_subscriber_id(self) -> str:
        """Generate a unique subscriber ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def subscribe_to_guests(self) -> EventSourceResponse:
        """Subscribe to guest updates"""
        subscriber_id = self.generate_subscriber_id()
        self.guest_subscribers.add(subscriber_id)
        
        async def event_generator():
            try:
                # Send initial connection message
                yield {
                    "event": "connected",
                    "data": json.dumps({
                        "subscriber_id": subscriber_id,
                        "message": "Connected to guest updates"
                    })
                }
                
                # Keep connection alive
                while subscriber_id in self.guest_subscribers:
                    await asyncio.sleep(1)
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now().isoformat()})
                    }
                    
            except asyncio.CancelledError:
                # Clean up when connection is closed
                self.guest_subscribers.discard(subscriber_id)
                yield {
                    "event": "disconnected",
                    "data": json.dumps({"message": "Disconnected from guest updates"})
                }
        
        return EventSourceResponse(event_generator())
    
    async def subscribe_to_reservations(self, guest_id: int) -> EventSourceResponse:
        """Subscribe to reservation updates for a specific guest"""
        subscriber_id = self.generate_subscriber_id()
        
        if guest_id not in self.reservation_subscribers:
            self.reservation_subscribers[guest_id] = set()
        self.reservation_subscribers[guest_id].add(subscriber_id)
        
        async def event_generator():
            try:
                # Send initial connection message
                yield {
                    "event": "connected",
                    "data": json.dumps({
                        "subscriber_id": subscriber_id,
                        "guest_id": guest_id,
                        "message": f"Connected to reservation updates for guest {guest_id}"
                    })
                }
                
                # Keep connection alive
                while (guest_id in self.reservation_subscribers and 
                       subscriber_id in self.reservation_subscribers[guest_id]):
                    await asyncio.sleep(1)
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": datetime.now().isoformat()})
                    }
                    
            except asyncio.CancelledError:
                # Clean up when connection is closed
                if guest_id in self.reservation_subscribers:
                    self.reservation_subscribers[guest_id].discard(subscriber_id)
                    if not self.reservation_subscribers[guest_id]:
                        del self.reservation_subscribers[guest_id]
                yield {
                    "event": "disconnected",
                    "data": json.dumps({"message": "Disconnected from reservation updates"})
                }
        
        return EventSourceResponse(event_generator())
    
    async def notify_guest_created(self, guest: GuestResponse):
        """Notify all subscribers about a new guest"""
        if not self.guest_subscribers:
            return
        
        event_data = {
            "event_type": "guest_created",
            "guest": guest.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, you would send this to all subscribers
        # For now, we'll just log it
        print(f"Guest created event: {event_data}")
    
    async def notify_guest_updated(self, guest: GuestResponse):
        """Notify all subscribers about a guest update"""
        if not self.guest_subscribers:
            return
        
        event_data = {
            "event_type": "guest_updated",
            "guest": guest.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, you would send this to all subscribers
        # For now, we'll just log it
        print(f"Guest updated event: {event_data}")
    
    async def notify_reservation_created(self, reservation: ReservationWithDetails):
        """Notify guest subscribers about a new reservation"""
        guest_id = reservation.guest_id
        if guest_id not in self.reservation_subscribers:
            return
        
        event_data = {
            "event_type": "reservation_created",
            "reservation": reservation.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, you would send this to all subscribers
        # For now, we'll just log it
        print(f"Reservation created event for guest {guest_id}: {event_data}")
    
    async def notify_reservation_updated(self, reservation: ReservationWithDetails):
        """Notify guest subscribers about a reservation update"""
        guest_id = reservation.guest_id
        if guest_id not in self.reservation_subscribers:
            return
        
        event_data = {
            "event_type": "reservation_updated",
            "reservation": reservation.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, you would send this to all subscribers
        # For now, we'll just log it
        print(f"Reservation updated event for guest {guest_id}: {event_data}")
    
    async def notify_reservation_cancelled(self, reservation: ReservationWithDetails):
        """Notify guest subscribers about a cancelled reservation"""
        guest_id = reservation.guest_id
        if guest_id not in self.reservation_subscribers:
            return
        
        event_data = {
            "event_type": "reservation_cancelled",
            "reservation": reservation.model_dump(),
            "timestamp": datetime.now().isoformat()
        }
        
        # In a real implementation, you would send this to all subscribers
        # For now, we'll just log it
        print(f"Reservation cancelled event for guest {guest_id}: {event_data}")


# Global SSE service instance
sse_service = SSEService() 