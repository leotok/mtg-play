from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """Get user by email or username"""
        return self.db.query(User).filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()
    
    def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def username_exists(self, username: str) -> bool:
        """Check if username exists"""
        return self.db.query(User).filter(User.username == username).first() is not None
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get only active users"""
        return self.db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def get_inactive_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get only inactive users"""
        return self.db.query(User).filter(User.is_active == False).offset(skip).limit(limit).all()
    
    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by username or email"""
        search_pattern = f"%{query}%"
        return self.db.query(User).filter(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        ).limit(limit).all()
    
    def get_users_created_after(self, date) -> List[User]:
        """Get users created after a specific date"""
        return self.db.query(User).filter(User.created_at >= date).all()
    
    def get_users_created_between(self, start_date, end_date) -> List[User]:
        """Get users created between two dates"""
        return self.db.query(User).filter(
            and_(User.created_at >= start_date, User.created_at <= end_date)
        ).all()
    
    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        from datetime import datetime
        
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate a user account"""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            return True
        return False
    
    def activate_user(self, user_id: int) -> bool:
        """Activate a user account"""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            return True
        return False
    
    def verify_email(self, user_id: int) -> bool:
        """Mark user's email as verified"""
        user = self.get_by_id(user_id)
        if user:
            user.email_verified = True
            self.db.commit()
            return True
        return False
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        user = self.get_by_id(user_id)
        if not user:
            return {}
        
        # Count decks
        deck_count = len(user.decks) if user.decks else 0
        
        # Count total cards across all decks
        total_cards = 0
        if user.decks:
            for deck in user.decks:
                for deck_card in deck.cards:
                    total_cards += deck_card.quantity
        
        # Count unique cards
        unique_cards = set()
        if user.decks:
            for deck in user.decks:
                for deck_card in deck.cards:
                    unique_cards.add(deck_card.card_scryfall_id)
        
        return {
            "deck_count": deck_count,
            "total_cards": total_cards,
            "unique_cards": len(unique_cards),
            "avg_deck_size": total_cards / deck_count if deck_count > 0 else 0,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat(),
            "email_verified": user.email_verified
        }
