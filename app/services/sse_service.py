import asyncio
import json
from typing import Dict, Set, Optional
from sse_starlette.sse import EventSourceResponse
from app.schemas.guest import GuestResponse
from app.schemas.reservation import ReservationResponse
import logging

logger = logging.getLogger(__name__)


class SSEService:
    """Service for managing Server-Sent Events (SSE) connections"""
    
    def __init__(self):
        self.connections: Set[asyncio.Queue] = set()
        self.guest_connections: Dict[int, Set[asyncio.Queue]] = {}
        self.reservation_connections: Dict[int, Set[asyncio.Queue]] = {}
    
    async def add_connection(self, queue: asyncio.Queue):
        """Add a new SSE connection"""
        self.connections.add(queue)
        logger.info(f"Added SSE connection, total connections: {len(self.connections)}")
    
    async def remove_connection(self, queue: asyncio.Queue):
        """Remove an SSE connection"""
        self.connections.discard(queue)
        logger.info(f"Removed SSE connection, total connections: {len(self.connections)}")
    
    async def add_guest_connection(self, guest_id: int, queue: asyncio.Queue):
        """Add a new SSE connection for a specific guest"""
        if guest_id not in self.guest_connections:
            self.guest_connections[guest_id] = set()
        self.guest_connections[guest_id].add(queue)
        logger.info(f"Added guest SSE connection for guest {guest_id}")
    
    async def remove_guest_connection(self, guest_id: int, queue: asyncio.Queue):
        """Remove an SSE connection for a specific guest"""
        if guest_id in self.guest_connections:
            self.guest_connections[guest_id].discard(queue)
            if not self.guest_connections[guest_id]:
                del self.guest_connections[guest_id]
        logger.info(f"Removed guest SSE connection for guest {guest_id}")
    
    async def add_reservation_connection(self, guest_id: int, queue: asyncio.Queue):
        """Add a new SSE connection for reservation updates for a specific guest"""
        if guest_id not in self.reservation_connections:
            self.reservation_connections[guest_id] = set()
        self.reservation_connections[guest_id].add(queue)
        logger.info(f"Added reservation SSE connection for guest {guest_id}")
    
    async def remove_reservation_connection(self, guest_id: int, queue: asyncio.Queue):
        """Remove an SSE connection for reservation updates for a specific guest"""
        if guest_id in self.reservation_connections:
            self.reservation_connections[guest_id].discard(queue)
            if not self.reservation_connections[guest_id]:
                del self.reservation_connections[guest_id]
        logger.info(f"Removed reservation SSE connection for guest {guest_id}")
    
    async def broadcast_guest_created(self, guest: GuestResponse):
        """Broadcast guest creation event to all connections"""
        event_data = {
            "type": "guest_created",
            "data": guest.model_dump()
        }
        
        # Broadcast to all general connections
        await self._broadcast_to_connections(self.connections, event_data)
        
        # Broadcast to guest-specific connections
        if guest.id in self.guest_connections:
            await self._broadcast_to_connections(self.guest_connections[guest.id], event_data)
    
    async def broadcast_guest_updated(self, guest: GuestResponse):
        """Broadcast guest update event to all connections"""
        event_data = {
            "type": "guest_updated",
            "data": guest.model_dump()
        }
        
        # Broadcast to all general connections
        await self._broadcast_to_connections(self.connections, event_data)
        
        # Broadcast to guest-specific connections
        if guest.id in self.guest_connections:
            await self._broadcast_to_connections(self.guest_connections[guest.id], event_data)
    
    async def broadcast_reservation_created(self, reservation: ReservationResponse, guest_id: int):
        """Broadcast reservation creation event to guest-specific connections"""
        event_data = {
            "type": "reservation_created",
            "data": reservation.model_dump()
        }
        
        # Broadcast to guest-specific reservation connections
        if guest_id in self.reservation_connections:
            await self._broadcast_to_connections(self.reservation_connections[guest_id], event_data)
    
    async def broadcast_reservation_updated(self, reservation: ReservationResponse, guest_id: int):
        """Broadcast reservation update event to guest-specific connections"""
        event_data = {
            "type": "reservation_updated",
            "data": reservation.model_dump()
        }
        
        # Broadcast to guest-specific reservation connections
        if guest_id in self.reservation_connections:
            await self._broadcast_to_connections(self.reservation_connections[guest_id], event_data)
    
    async def broadcast_reservation_cancelled(self, reservation: ReservationResponse, guest_id: int):
        """Broadcast reservation cancellation event to guest-specific connections"""
        event_data = {
            "type": "reservation_cancelled",
            "data": reservation.model_dump()
        }
        
        # Broadcast to guest-specific reservation connections
        if guest_id in self.reservation_connections:
            await self._broadcast_to_connections(self.reservation_connections[guest_id], event_data)
    
    async def _broadcast_to_connections(self, connections: Set[asyncio.Queue], event_data: Dict):
        """Broadcast event to a set of connections"""
        if not connections:
            return
        
        # Convert event data to SSE format
        sse_data = f"data: {json.dumps(event_data)}\n\n"
        
        # Send to all connections
        for queue in connections.copy():
            try:
                await queue.put(sse_data)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                # Remove broken connection
                connections.discard(queue)
    
    async def subscribe_to_guests(self):
        """Subscribe to general guest updates"""
        queue = asyncio.Queue()
        await self.add_connection(queue)
        
        try:
            async def event_generator():
                while True:
                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield data
                    except asyncio.TimeoutError:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': '2024-01-01T00:00:00Z'})}\n\n"
            
            return EventSourceResponse(event_generator())
        finally:
            await self.remove_connection(queue)
    
    async def subscribe_to_guest_updates(self, guest_id: int):
        """Subscribe to updates for a specific guest"""
        queue = asyncio.Queue()
        await self.add_guest_connection(guest_id, queue)
        
        try:
            async def event_generator():
                while True:
                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield data
                    except asyncio.TimeoutError:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': '2024-01-01T00:00:00Z'})}\n\n"
            
            return EventSourceResponse(event_generator())
        finally:
            await self.remove_guest_connection(guest_id, queue)
    
    async def subscribe_to_reservations(self, guest_id: int):
        """Subscribe to reservation updates for a specific guest"""
        queue = asyncio.Queue()
        await self.add_reservation_connection(guest_id, queue)
        
        try:
            async def event_generator():
                while True:
                    try:
                        data = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield data
                    except asyncio.TimeoutError:
                        # Send heartbeat to keep connection alive
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': '2024-01-01T00:00:00Z'})}\n\n"
            
            return EventSourceResponse(event_generator())
        finally:
            await self.remove_reservation_connection(guest_id, queue)


# Global SSE service instance
sse_service = SSEService() 