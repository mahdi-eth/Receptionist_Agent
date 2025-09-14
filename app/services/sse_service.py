import asyncio
import json
from typing import Dict, Optional, List
from fastapi.responses import StreamingResponse
from app.schemas.guest import GuestResponse
from app.schemas.reservation import ReservationResponse
from app.schemas.room import RoomResponse
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SSEClient:
    """SSE client connection handler."""
    
    def __init__(self, client_id: str, event_type: str, target_id: Optional[str] = None):
        self.client_id = client_id
        self.event_type = event_type
        self.target_id = target_id
        self.queue = asyncio.Queue()
        self.is_active = True
        self.created_at = datetime.now()
    
    async def send_event(self, event_type: str, data: dict) -> bool:
        """Send event to client."""
        if not self.is_active:
            return False
        
        try:
            sse_data = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
            await self.queue.put(sse_data)
            return True
        except Exception as e:
            logger.error(f"Failed to send event to client {self.client_id}: {e}")
            self.is_active = False
            return False
    
    async def get_event(self, timeout: float = 30.0) -> str:
        """Get next event from queue with heartbeat fallback."""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
    
    def close(self):
        """Close client and cleanup resources."""
        self.is_active = False
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break


class SSEService:
    """Server-Sent Events service for real-time updates."""
    
    def __init__(self):
        self._clients: Dict[str, Dict[str, SSEClient]] = {
            'guest': {},
            'session': {},
            'global': {},
        }
        self._client_counter = 0
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Initialize background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_clients())
    
    async def _cleanup_inactive_clients(self):
        """Background task to remove inactive clients."""
        while True:
            try:
                await asyncio.sleep(60)
                current_time = datetime.now()
                clients_to_remove = []
                
                for client_type, clients in self._clients.items():
                    for client_id, client in list(clients.items()):
                        if not client.is_active or (current_time - client.created_at).seconds > 300:
                            clients_to_remove.append((client_type, client_id))
                
                for client_type, client_id in clients_to_remove:
                    if client_id in self._clients[client_type]:
                        client = self._clients[client_type].pop(client_id)
                        client.close()
                        logger.info(f"Cleaned up inactive SSE client: {client_id}")
                        
            except Exception as e:
                logger.error(f"Error in SSE cleanup task: {e}")
    
    def _generate_client_id(self) -> str:
        """Generate unique client identifier."""
        self._client_counter += 1
        return f"sse_client_{self._client_counter}_{datetime.now().timestamp()}"
    
    async def _add_client(self, client_type: str, target_id: Optional[str] = None) -> SSEClient:
        """Register new SSE client."""
        client_id = self._generate_client_id()
        client = SSEClient(client_id, client_type, target_id)
        
        if target_id:
            self._clients[client_type][target_id] = client
        else:
            self._clients[client_type][client_id] = client
        
        logger.info(f"Added SSE client: {client_id} for {client_type}:{target_id}")
        return client
    
    async def _remove_client(self, client_type: str, target_id: str):
        """Unregister SSE client."""
        if target_id in self._clients[client_type]:
            client = self._clients[client_type].pop(target_id)
            client.close()
            logger.info(f"Removed SSE client: {target_id}")
    
    async def _broadcast_to_clients(self, client_type: str, event_type: str, data: dict, target_id: Optional[str] = None):
        """Broadcast event to specified client type."""
        clients_to_remove = []
        
        if target_id and target_id in self._clients[client_type]:
            client = self._clients[client_type][target_id]
            success = await client.send_event(event_type, data)
            if not success:
                clients_to_remove.append((client_type, target_id))
        else:
            for client_id, client in list(self._clients[client_type].items()):
                success = await client.send_event(event_type, data)
                if not success:
                    clients_to_remove.append((client_type, client_id))
        
        for client_type, client_id in clients_to_remove:
            if client_id in self._clients[client_type]:
                self._clients[client_type].pop(client_id)
    
    async def notify_guest_created(self, guest: GuestResponse, session_id: str = None):
        """Notify clients of guest creation."""
        guest_data = guest.model_dump()
        
        if session_id:
            await self._broadcast_to_clients('session', 'guest_created', guest_data, session_id)
            if session_id in self._clients['session']:
                session_client = self._clients['session'].pop(session_id)
                self._clients['guest'][str(guest.id)] = session_client
                session_client.target_id = str(guest.id)
        
        await self._broadcast_to_clients('guest', 'guest_created', guest_data, str(guest.id))
    
    async def notify_guest_updated(self, guest: GuestResponse):
        """Notify clients of guest updates."""
        guest_data = guest.model_dump()
        await self._broadcast_to_clients('guest', 'guest_updated', guest_data, str(guest.id))
    
    async def notify_rooms_updated(self, rooms: List[RoomResponse]):
        """Notify clients of room list changes."""
        room_data = [room.model_dump() for room in rooms]
        await self._broadcast_to_clients('global', 'rooms_updated', {'rooms': room_data})
    
    async def notify_reservation_created(self, reservation: ReservationResponse, guest_id: int):
        """Notify guest of reservation creation."""
        reservation_data = reservation.model_dump()
        await self._broadcast_to_clients('guest', 'reservation_created', reservation_data, str(guest_id))
    
    async def notify_reservation_updated(self, reservation: ReservationResponse, guest_id: int):
        """Notify guest of reservation updates."""
        reservation_data = reservation.model_dump()
        await self._broadcast_to_clients('guest', 'reservation_updated', reservation_data, str(guest_id))
    
    async def notify_reservation_cancelled(self, reservation: ReservationResponse, guest_id: int):
        """Notify guest of reservation cancellation."""
        reservation_data = reservation.model_dump()
        await self._broadcast_to_clients('guest', 'reservation_cancelled', reservation_data, str(guest_id))
    
    async def subscribe_to_guest_updates(self, guest_id: int):
        """Create SSE stream for guest updates."""
        client = await self._add_client('guest', str(guest_id))
        
        async def event_generator():
            try:
                while client.is_active:
                    try:
                        event_data = await client.get_event(timeout=30.0)
                        yield event_data
                    except Exception as e:
                        logger.error(f"Error in guest SSE stream: {e}")
                        break
            finally:
                await self._remove_client('guest', str(guest_id))
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    async def subscribe_to_room_updates(self):
        """Create SSE stream for room updates."""
        client = await self._add_client('global')
        
        async def event_generator():
            try:
                while client.is_active:
                    try:
                        event_data = await client.get_event(timeout=30.0)
                        yield event_data
                    except Exception as e:
                        logger.error(f"Error in room SSE stream: {e}")
                        break
            finally:
                await self._remove_client('global', client.client_id)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    async def subscribe_to_session_updates(self, session_id: str):
        """Create SSE stream for session updates."""
        client = await self._add_client('session', session_id)
        
        async def event_generator():
            try:
                while client.is_active:
                    try:
                        event_data = await client.get_event(timeout=30.0)
                        yield event_data
                    except Exception as e:
                        logger.error(f"Error in session SSE stream: {e}")
                        break
            finally:
                await self._remove_client('session', session_id)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
    
    async def subscribe_to_reservation_updates(self, guest_id: int):
        """Create SSE stream for reservation updates."""
        return await self.subscribe_to_guest_updates(guest_id)
    
    def get_client_stats(self) -> dict:
        """Get active client connection statistics."""
        return {
            'guest_clients': len(self._clients['guest']),
            'session_clients': len(self._clients['session']),
            'global_clients': len(self._clients['global']),
            'total_clients': sum(len(clients) for clients in self._clients.values())
        }


sse_service = SSEService() 