from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import os

# Use SQLite for development if PostgreSQL is not available
if settings.USE_SQLITE:
    DATABASE_URL = "sqlite:///./commander.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
else:
    DATABASE_URL = settings.DATABASE_URL
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
