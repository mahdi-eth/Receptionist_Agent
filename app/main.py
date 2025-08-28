from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import async_engine
from app.controllers import guest_router, room_router, reservation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting Hotel Receptionist API...")
    
    # Create database tables (in production, use Alembic migrations)
    async with async_engine.begin() as conn:
        from app.models import Base
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created/verified")
    print("Hotel Receptionist API started successfully!")
    
    yield
    
    # Shutdown
    print("Shutting down Hotel Receptionist API...")
    await async_engine.dispose()
    print("Hotel Receptionist API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A professional hotel receptionist management system with real-time updates",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc) if settings.debug else "Internal server error"
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": "2024-01-01T00:00:00Z"  # You can use datetime.now().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Hotel Receptionist API",
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }

# Include routers
app.include_router(guest_router, prefix="/api/v1")
app.include_router(room_router, prefix="/api/v1")
app.include_router(reservation_router, prefix="/api/v1")

# System-wide SSE endpoint
@app.get("/api/v1/sse/system-updates", tags=["SSE - Real-time Updates"], include_in_schema=True)
async def subscribe_to_system_updates():
    """
    Subscribe to system-wide real-time updates via Server-Sent Events
    
    This endpoint establishes a Server-Sent Events connection that will send real-time updates
    for all system events including guests, rooms, and reservations.
    
    Returns:
        EventSourceResponse: A streaming response with real-time system updates
    """
    from app.services.sse_service import sse_service
    return await sse_service.subscribe_to_guests()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 