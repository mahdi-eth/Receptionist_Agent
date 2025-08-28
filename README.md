# Hotel Receptionist API

A professional, scalable FastAPI-based hotel receptionist management system with real-time updates via Server-Sent Events (SSE).

## Features

- **Guests Management**: Complete CRUD operations for guest information
- **Rooms Management**: Room inventory and status tracking
- **Reservations System**: Booking management with conflict detection
- **Real-time Updates**: SSE endpoints for live guest and reservation updates
- **Clean Architecture**: Repository-Service-Controller pattern
- **Async Operations**: Full async/await support throughout the stack
- **Database Migrations**: Alembic for schema management
- **Professional Structure**: Production-ready code organization

## Architecture

The project follows a clean, layered architecture:

```
app/
├── controllers/     # API endpoints and request handling
├── services/        # Business logic and validation
├── repositories/    # Data access layer
├── models/          # SQLAlchemy database models
├── schemas/         # Pydantic request/response models
├── database.py      # Database configuration
├── config.py        # Application settings
└── main.py          # FastAPI application entry point
```

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Primary database
- **Qdrant**: Vector database for future AI features
- **Alembic**: Database migration tool
- **Pydantic**: Data validation and settings management
- **SSE-Starlette**: Server-Sent Events implementation

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- PostgreSQL (via Docker)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Receptionist_Agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the environment example file and configure your settings:

```bash
cp env.example .env
# Edit .env with your database credentials
```

### 5. Start Database Services

```bash
docker-compose up -d postgres qdrant
```

### 6. Run Database Migrations

```bash
alembic upgrade head
```

### 7. Start the Application

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

## API Documentation

### Base URL
```
http://localhost:8000/api/v1
```

### Endpoints

#### Guests
- `POST /guests/` - Create a new guest
- `GET /guests/` - List all guests (with pagination and search)
- `GET /guests/{guest_id}` - Get specific guest
- `PUT /guests/{guest_id}` - Update guest
- `DELETE /guests/{guest_id}` - Soft delete guest
- `GET /guests/search?q={search_term}` - Search guests
- `GET /guests/sse/updates` - Subscribe to guest updates (SSE)

#### Rooms
- `POST /rooms/` - Create a new room
- `GET /rooms/` - List all rooms (with filters)
- `GET /rooms/{room_id}` - Get specific room
- `PUT /rooms/{room_id}` - Update room
- `DELETE /rooms/{room_id}` - Soft delete room
- `GET /rooms/available` - Get available rooms
- `PATCH /rooms/{room_id}/status` - Update room status

#### Reservations
- `POST /reservations/` - Create a new reservation
- `GET /reservations/` - List all reservations (with filters)
- `GET /reservations/{reservation_id}` - Get specific reservation
- `PUT /reservations/{reservation_id}` - Update reservation
- `DELETE /reservations/{reservation_id}` - Soft delete reservation
- `POST /reservations/{reservation_id}/cancel` - Cancel reservation
- `GET /reservations/guest/{guest_id}` - Get guest reservations
- `GET /reservations/guest/{guest_id}/sse/updates` - Subscribe to guest reservation updates (SSE)

### Interactive API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Database Schema

### Guests Table
- Comprehensive guest information (name, email, phone, address, etc.)
- Soft delete support
- Timestamps for audit trail

### Rooms Table
- Room details (number, type, floor, capacity, price)
- Status tracking (available, occupied, maintenance, etc.)
- Amenities and description fields

### Reservations Table
- Booking information with guest and room relationships
- Date range validation and conflict detection
- Status tracking and cancellation support
- Unique reservation numbers

## Real-time Updates

The system provides real-time updates using Server-Sent Events (SSE):

1. **Guest Updates**: Subscribe to `/guests/sse/updates` for live guest changes
2. **Reservation Updates**: Subscribe to `/reservations/guest/{guest_id}/sse/updates` for guest-specific reservation changes

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints throughout
- Comprehensive docstrings for all functions
- Async/await for all I/O operations

### Testing
```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Production Considerations

- Configure proper CORS settings
- Set up environment-specific configurations
- Implement proper logging
- Add authentication and authorization
- Set up monitoring and health checks
- Configure database connection pooling
- Implement rate limiting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or support, please open an issue in the repository. 