from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
from .user import UserRepository
from .deck import DeckRepository
from .user_session import UserSessionRepository


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency injection for UserRepository"""
    return UserRepository(db)


def get_deck_repository(db: Session = Depends(get_db)) -> DeckRepository:
    """Dependency injection for DeckRepository"""
    return DeckRepository(db)


def get_user_session_repository(db: Session = Depends(get_db)) -> UserSessionRepository:
    """Dependency injection for UserSessionRepository"""
    return UserSessionRepository(db)
