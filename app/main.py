from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import async_engine
from app.controllers import guest_router, room_router, reservation_router, chat_router, streaming_chat_router
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import create_tables
    await create_tables()
    yield
    await async_engine.dispose()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Hotel receptionist management system with real-time updates",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error": str(exc) if settings.debug else "Internal server error"
        }
    )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    return {
        "message": "Welcome to Hotel Receptionist API",
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }

app.include_router(guest_router, prefix="/api/v1")
app.include_router(room_router, prefix="/api/v1")
app.include_router(reservation_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(streaming_chat_router, prefix="/api/v1")

@app.get("/api/v1/sse/stats", tags=["SSE - Real-time Updates"], include_in_schema=True)
async def get_sse_stats():
    from app.services.sse_service import sse_service
    return sse_service.get_client_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 