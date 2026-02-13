import logging
import sys

# Configure logging BEFORE any other imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True  # Force reconfiguration
)

# Get uvicorn logger to work with uvicorn
logger = logging.getLogger("uvicorn")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.setLevel(logging.DEBUG)

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db, engine
from sqlalchemy import text
from app.api.v1 import auth, decks, cards, cache
from fastapi.responses import JSONResponse

app = FastAPI(
    title="MTG Commander Online",
    description="API for Magic: The Gathering Commander online platform",
    version="0.1.0",
    debug=True,
)

# Configure CORS - MUST be FIRST middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add logging middleware AFTER CORS
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"[REQUEST] {request.method} {request.url.path}")
    response = await call_next(request)
    logging.info(f"[RESPONSE] {response.status_code}")
    return response

# Include API routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(decks.router, prefix=settings.API_V1_PREFIX)
app.include_router(cards.router, prefix=settings.API_V1_PREFIX)
app.include_router(cache.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    logging.info("Root endpoint called")
    return {"message": "MTG Commander Online API", "version": "0.1.0"}


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database connectivity"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "version": "0.1.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "version": "0.1.0"
        }
