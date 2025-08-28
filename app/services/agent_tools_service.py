from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.guest_service import GuestService
from app.services.room_service import RoomService
from app.services.reservation_service import ReservationService
from app.schemas.guest import GuestCreate, GuestUpdate
from app.schemas.room import RoomResponse
from app.schemas.reservation import ReservationCreate, ReservationUpdate
from app.models.room import RoomStatus
from app.models.reservation import ReservationStatus
import logging

logger = logging.getLogger(__name__)


class AgentToolsService:
    """Service that provides tools for the AI agent to interact with the hotel system"""
    
    def __init__(self):
        self.guest_service = GuestService()
        self.room_service = RoomService()
        self.reservation_service = ReservationService()

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools for the agent"""
        return [
            {
                "name": "create_guest",
                "description": "Create a new guest profile",
                "parameters": {
                    "first_name": "string",
                    "last_name": "string", 
                    "email": "string",
                    "phone": "string (optional)",
                    "address": "string (optional)",
                    "city": "string (optional)",
                    "country": "string (optional)",
                    "postal_code": "string (optional)",
                    "nationality": "string (optional)",
                    "passport_number": "string (optional)"
                }
            },
            {
                "name": "update_guest",
                "description": "Update an existing guest profile",
                "parameters": {
                    "guest_id": "integer",
                    "first_name": "string (optional)",
                    "last_name": "string (optional)",
                    "email": "string (optional)",
                    "phone": "string (optional)",
                    "address": "string (optional)",
                    "city": "string (optional)",
                    "country": "string (optional)",
                    "postal_code": "string (optional)",
                    "nationality": "string (optional)",
                    "passport_number": "string (optional)"
                }
            },
            {
                "name": "get_guest",
                "description": "Get guest information by ID",
                "parameters": {
                    "guest_id": "integer"
                }
            },
            {
                "name": "search_guests",
                "description": "Search guests by name or email",
                "parameters": {
                    "search_term": "string",
                    "limit": "integer (optional, default 10)"
                }
            },
            {
                "name": "get_all_rooms",
                "description": "Get information about all rooms",
                "parameters": {
                    "limit": "integer (optional, default 100)"
                }
            },
            {
                "name": "get_available_rooms",
                "description": "Get only available rooms",
                "parameters": {
                    "limit": "integer (optional, default 100)"
                }
            },
            {
                "name": "get_rooms_by_type",
                "description": "Get rooms by specific type",
                "parameters": {
                    "room_type": "string (single|double|suite|deluxe|triple)",
                    "limit": "integer (optional, default 100)"
                }
            },
            {
                "name": "get_room_status",
                "description": "Get current status of a specific room",
                "parameters": {
                    "room_id": "integer"
                }
            },
            {
                "name": "create_reservation",
                "description": "Create a new reservation",
                "parameters": {
                    "guest_id": "integer",
                    "room_id": "integer",
                    "check_in_date": "string (YYYY-MM-DD)",
                    "check_out_date": "string (YYYY-MM-DD)",
                    "total_amount": "float",
                    "deposit_amount": "float (optional)",
                    "special_requests": "string (optional)"
                }
            },
            {
                "name": "update_reservation",
                "description": "Update an existing reservation",
                "parameters": {
                    "reservation_id": "integer",
                    "check_in_date": "string (YYYY-MM-DD, optional)",
                    "check_out_date": "string (YYYY-MM-DD, optional)",
                    "total_amount": "float (optional)",
                    "deposit_amount": "float (optional)",
                    "special_requests": "string (optional)"
                }
            },
            {
                "name": "cancel_reservation",
                "description": "Cancel a reservation",
                "parameters": {
                    "reservation_id": "integer",
                    "reason": "string",
                    "cancelled_by": "string"
                }
            },
            {
                "name": "get_guest_reservations",
                "description": "Get all reservations for a specific guest",
                "parameters": {
                    "guest_id": "integer",
                    "limit": "integer (optional, default 100)"
                }
            }
        ]

    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        try:
            if tool_name == "create_guest":
                return await self._create_guest(parameters, db)
            elif tool_name == "update_guest":
                return await self._update_guest(parameters, db)
            elif tool_name == "get_guest":
                return await self._get_guest(parameters, db)
            elif tool_name == "search_guests":
                return await self._search_guests(parameters, db)
            elif tool_name == "get_all_rooms":
                return await self._get_all_rooms(parameters, db)
            elif tool_name == "get_available_rooms":
                return await self._get_available_rooms(parameters, db)
            elif tool_name == "get_rooms_by_type":
                return await self._get_rooms_by_type(parameters, db)
            elif tool_name == "get_room_status":
                return await self._get_room_status(parameters, db)
            elif tool_name == "create_reservation":
                return await self._create_reservation(parameters, db)
            elif tool_name == "update_reservation":
                return await self._update_reservation(parameters, db)
            elif tool_name == "cancel_reservation":
                return await self._cancel_reservation(parameters, db)
            elif tool_name == "get_guest_reservations":
                return await self._get_guest_reservations(parameters, db)
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_guest(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Create a new guest"""
        try:
            guest_data = GuestCreate(**params)
            guest = await self.guest_service.create_guest(db, guest_data)
            return {
                "success": True,
                "message": f"Guest {guest.first_name} {guest.last_name} created successfully",
                "guest_id": guest.id,
                "guest": {
                    "id": guest.id,
                    "first_name": guest.first_name,
                    "last_name": guest.last_name,
                    "email": guest.email
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _update_guest(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Update an existing guest"""
        try:
            guest_id = params.pop("guest_id")
            guest_data = GuestUpdate(**params)
            guest = await self.guest_service.update_guest(db, guest_id, guest_data)
            return {
                "success": True,
                "message": f"Guest {guest.first_name} {guest.last_name} updated successfully",
                "guest_id": guest.id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_guest(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get guest information"""
        try:
            guest_id = params["guest_id"]
            guest = await self.guest_service.get_guest(db, guest_id)
            return {
                "success": True,
                "guest": {
                    "id": guest.id,
                    "first_name": guest.first_name,
                    "last_name": guest.last_name,
                    "email": guest.email,
                    "phone": guest.phone,
                    "address": guest.address,
                    "city": guest.city,
                    "country": guest.country
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search_guests(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Search guests"""
        try:
            search_term = params["search_term"]
            limit = params.get("limit", 10)
            result = await self.guest_service.search_guests(db, search_term, 0, limit)
            return {
                "success": True,
                "guests": [
                    {
                        "id": guest.id,
                        "first_name": guest.first_name,
                        "last_name": guest.last_name,
                        "email": guest.email
                    } for guest in result.guests
                ],
                "total": result.total
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_all_rooms(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get all rooms"""
        try:
            limit = params.get("limit", 100)
            result = await self.room_service.get_rooms(db, 0, limit)
            return {
                "success": True,
                "rooms": [
                    {
                        "id": room.id,
                        "room_number": room.room_number,
                        "room_type": room.room_type.value,
                        "status": room.status.value,
                        "floor": room.floor,
                        "capacity": room.capacity,
                        "price_per_night": float(room.price_per_night),
                        "description": room.description
                    } for room in result.rooms
                ],
                "total": result.total
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_available_rooms(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get available rooms"""
        try:
            limit = params.get("limit", 100)
            result = await self.room_service.get_available_rooms(db, 0, limit)
            return {
                "success": True,
                "rooms": [
                    {
                        "id": room.id,
                        "room_number": room.room_number,
                        "room_type": room.room_type.value,
                        "floor": room.floor,
                        "capacity": room.capacity,
                        "price_per_night": float(room.price_per_night),
                        "description": room.description
                    } for room in result.rooms
                ],
                "total": result.total
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_rooms_by_type(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get rooms by type"""
        try:
            room_type = params["room_type"]
            limit = params.get("limit", 100)
            result = await self.room_service.get_rooms(db, 0, limit, room_type=room_type)
            return {
                "success": True,
                "rooms": [
                    {
                        "id": room.id,
                        "room_number": room.room_number,
                        "room_type": room.room_type.value,
                        "status": room.status.value,
                        "floor": room.floor,
                        "capacity": room.capacity,
                        "price_per_night": float(room.price_per_night),
                        "description": room.description
                    } for room in result.rooms
                ],
                "total": result.total
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_room_status(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get room status"""
        try:
            room_id = params["room_id"]
            room = await self.room_service.get_room(db, room_id)
            return {
                "success": True,
                "room": {
                    "id": room.id,
                    "room_number": room.room_number,
                    "status": room.status.value,
                    "room_type": room.room_type.value,
                    "floor": room.floor,
                    "capacity": room.capacity,
                    "price_per_night": float(room.price_per_night)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _create_reservation(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Create a reservation"""
        try:
            # Convert date strings to datetime objects
            from datetime import datetime
            if "check_in_date" in params:
                params["check_in_date"] = datetime.fromisoformat(params["check_in_date"])
            if "check_out_date" in params:
                params["check_out_date"] = datetime.fromisoformat(params["check_out_date"])
            
            reservation_data = ReservationCreate(**params)
            reservation = await self.reservation_service.create_reservation(db, reservation_data)
            return {
                "success": True,
                "message": f"Reservation {reservation.reservation_number} created successfully",
                "reservation_id": reservation.id,
                "reservation_number": reservation.reservation_number
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _update_reservation(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Update a reservation"""
        try:
            reservation_id = params.pop("reservation_id")
            
            # Convert date strings to datetime objects
            from datetime import datetime
            if "check_in_date" in params:
                params["check_in_date"] = datetime.fromisoformat(params["check_in_date"])
            if "check_out_date" in params:
                params["check_out_date"] = datetime.fromisoformat(params["check_out_date"])
            
            reservation_data = ReservationUpdate(**params)
            reservation = await self.reservation_service.update_reservation(db, reservation_id, reservation_data)
            return {
                "success": True,
                "message": f"Reservation {reservation.reservation_number} updated successfully",
                "reservation_id": reservation.id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _cancel_reservation(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Cancel a reservation"""
        try:
            reservation_id = params["reservation_id"]
            reason = params["reason"]
            cancelled_by = params["cancelled_by"]
            
            reservation = await self.reservation_service.cancel_reservation(db, reservation_id, reason, cancelled_by)
            return {
                "success": True,
                "message": f"Reservation {reservation.reservation_number} cancelled successfully",
                "reservation_id": reservation.id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_guest_reservations(self, params: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Get guest reservations"""
        try:
            guest_id = params["guest_id"]
            limit = params.get("limit", 100)
            result = await self.reservation_service.get_guest_reservations(db, guest_id, 0, limit)
            return {
                "success": True,
                "reservations": [
                    {
                        "id": res.id,
                        "reservation_number": res.reservation_number,
                        "check_in_date": res.check_in_date.isoformat(),
                        "check_out_date": res.check_out_date.isoformat(),
                        "status": res.status.value,
                        "total_amount": float(res.total_amount),
                        "room_number": res.room_number,
                        "room_type": res.room_type
                    } for res in result.reservations
                ],
                "total": result.total
            }
        except Exception as e:
            return {"success": False, "error": str(e)} 