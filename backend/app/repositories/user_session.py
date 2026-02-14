from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, UTC

from app.models.user import UserSession
from .base import BaseRepository


class UserSessionRepository(BaseRepository[UserSession]):
    """Repository for UserSession model operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, UserSession)
    
    def get_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """Get session by refresh token"""
        return self.db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()
    
    def get_active_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user"""
        return self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(UTC)
            )
        ).all()
    
    def get_active_session_count(self, user_id: int) -> int:
        """Count active sessions for a user"""
        return self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(UTC)
            )
        ).count()
    
    def create_session(self, user_id: int, refresh_token: str, expires_at: datetime) -> UserSession:
        """Create a new user session"""
        session_data = {
            "user_id": user_id,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "is_active": True
        }
        return self.create(session_data)
    
    def invalidate_session(self, session_id: int) -> bool:
        """Invalidate a specific session"""
        session = self.get_by_id(session_id)
        if session:
            session.is_active = False
            self.db.commit()
            return True
        return False
    
    def invalidate_user_sessions(self, user_id: int) -> int:
        """Invalidate all sessions for a user"""
        count = self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).update({"is_active": False})
        
        self.db.commit()
        return count
    
    def invalidate_session_by_token(self, refresh_token: str) -> bool:
        """Invalidate session by refresh token"""
        session = self.get_by_refresh_token(refresh_token)
        if session:
            session.is_active = False
            self.db.commit()
            return True
        return False
    
    def cleanup_expired_sessions(self, user_id: Optional[int] = None) -> int:
        """Clean up expired sessions"""
        query = self.db.query(UserSession).filter(
            or_(
                UserSession.expires_at < datetime.now(UTC),
                UserSession.is_active == False
            )
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        count = query.count()
        query.delete()
        self.db.commit()
        return count
    
    def get_expired_sessions(self, user_id: Optional[int] = None) -> List[UserSession]:
        """Get expired sessions"""
        query = self.db.query(UserSession).filter(
            UserSession.expires_at < datetime.now(UTC)
        )
        
        if user_id:
            query = query.filter(UserSession.user_id == user_id)
        
        return query.all()
    
    def get_sessions_expiring_soon(self, hours: int = 24) -> List[UserSession]:
        """Get sessions that will expire soon"""
        soon = datetime.now(UTC) + timedelta(hours=hours)
        return self.db.query(UserSession).filter(
            and_(
                UserSession.expires_at <= soon,
                UserSession.expires_at > datetime.now(UTC),
                UserSession.is_active == True
            )
        ).all()
    
    def revoke_all_sessions(self, user_id: int) -> int:
        """Revoke all active sessions for a user (alias for invalidate_user_sessions)"""
        return self.invalidate_user_sessions(user_id)
    
    def is_session_valid(self, refresh_token: str) -> bool:
        """Check if a session is valid"""
        session = self.get_by_refresh_token(refresh_token)
        if not session:
            return False
        
        return (
            session.is_active and 
            session.expires_at > datetime.now(UTC)
        )
    
    def extend_session(self, session_id: int, days: int = 7) -> bool:
        """Extend session expiration"""
        session = self.get_by_id(session_id)
        if session and session.is_active:
            session.expires_at = datetime.now(UTC) + timedelta(days=days)
            self.db.commit()
            return True
        return False
