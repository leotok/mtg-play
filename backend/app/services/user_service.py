from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

from app.models.user import User, UserSession
from app.core.security import (
    get_password_hash, 
    verify_password, 
    validate_email,
    create_refresh_token,
    verify_token
)
from app.core.auth import login_rate_limiter, register_rate_limiter
from app.schemas.user import UserCreate, UserUpdate, UserPasswordChange
from app.repositories import (
    UserRepository,
    UserSessionRepository,
    get_user_repository,
    get_user_session_repository
)


class UserService:
    """User service with business logic, using repositories for data access"""
    
    def __init__(self, user_repo: UserRepository, session_repo: UserSessionRepository):
        self.user_repo = user_repo
        self.session_repo = session_repo
    
    @classmethod
    def create_with_repositories(cls, db_session):
        """Factory method to create service with repositories"""
        user_repo = UserRepository(db_session)
        session_repo = UserSessionRepository(db_session)
        return cls(user_repo, session_repo)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.user_repo.get_by_email(email)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.user_repo.get_by_username(username)
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user"""
        logger.info(f"Creating user - Email: {user_create.email}, Username: {user_create.username}")
        
        # Check rate limiting
        if register_rate_limiter.is_rate_limited(user_create.email):
            logger.warning(f"Rate limit hit for email: {user_create.email}")
            raise ValueError("Too many registration attempts. Please try again later.")
        
        # Validate email format
        if not validate_email(user_create.email):
            logger.warning(f"Invalid email format: {user_create.email}")
            raise ValueError("Invalid email format")
        
        # Check if user already exists
        if self.user_repo.email_exists(user_create.email):
            logger.warning(f"Email already registered: {user_create.email}")
            raise ValueError("Email already registered")
        
        if self.user_repo.username_exists(user_create.username):
            logger.warning(f"Username already taken: {user_create.username}")
            raise ValueError("Username already taken")
        
        # Create user
        hashed_password = get_password_hash(user_create.password)
        user_data = {
            "email": user_create.email,
            "username": user_create.username,
            "hashed_password": hashed_password,
            "is_active": True
        }
        
        user = self.user_repo.create(user_data)
        logger.info(f"User created successfully - ID: {user.id}, Email: {user.email}")
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        logger.info(f"Authenticating user - Email: {email}")
        
        # Check rate limiting
        if login_rate_limiter.is_rate_limited(email):
            logger.warning(f"Rate limit hit for login - Email: {email}")
            raise ValueError("Too many login attempts. Please try again later.")
        
        user = self.user_repo.get_by_email(email)
        if not user:
            logger.warning(f"User not found - Email: {email}")
            return None
        
        logger.debug(f"User found - ID: {user.id}, checking password")
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Invalid password - Email: {email}")
            return None
        
        if not user.is_active:
            logger.warning(f"Account inactive - User ID: {user.id}")
            raise ValueError("Account is inactive")
        
        # Update last login
        self.user_repo.update_last_login(user.id)
        logger.info(f"Authentication successful - User ID: {user.id}")
        
        return user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """Update user profile"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Prepare update data
        update_data = {}
        
        # Update email if provided
        if user_update.email and user_update.email != user.email:
            if not validate_email(user_update.email):
                raise ValueError("Invalid email format")
            
            if self.user_repo.email_exists(user_update.email):
                raise ValueError("Email already registered")
            
            update_data["email"] = user_update.email
        
        # Update username if provided
        if user_update.username and user_update.username != user.username:
            if self.user_repo.username_exists(user_update.username):
                raise ValueError("Username already taken")
            
            update_data["username"] = user_update.username
        
        # Update active status if provided
        if user_update.is_active is not None:
            update_data["is_active"] = user_update.is_active
        
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            return self.user_repo.update(user, update_data)
        
        return user
    
    def change_password(self, user_id: int, password_change: UserPasswordChange) -> bool:
        """Change user password"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify current password
        if not verify_password(password_change.current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        
        # Update password
        new_hashed_password = get_password_hash(password_change.new_password)
        update_data = {
            "hashed_password": new_hashed_password,
            "updated_at": datetime.utcnow()
        }
        
        self.user_repo.update(user, update_data)
        
        # Invalidate all existing sessions (force re-login)
        self.session_repo.invalidate_user_sessions(user_id)
        
        return True
    
    def invalidate_user_sessions(self, user_id: int):
        """Invalidate all user sessions"""
        return self.session_repo.invalidate_user_sessions(user_id)
    
    def create_user_session(self, user_id: int, refresh_token: str) -> UserSession:
        """Create a new user session"""
        # Clean up old inactive sessions
        self.session_repo.cleanup_expired_sessions(user_id)
        
        # Create new session
        expires_at = datetime.utcnow() + timedelta(days=7)
        return self.session_repo.create_session(user_id, refresh_token, expires_at)
    
    def get_user_session(self, refresh_token: str) -> Optional[UserSession]:
        """Get user session by refresh token"""
        return self.session_repo.get_by_refresh_token(refresh_token)
    
    def cleanup_old_sessions(self, user_id: Optional[int] = None):
        """Clean up old inactive sessions"""
        return self.session_repo.cleanup_expired_sessions(user_id)
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics"""
        return self.user_repo.get_user_stats(user_id)
    
    def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by username or email (admin function)"""
        return self.user_repo.search_users(query, limit)
    
    def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account"""
        return self.user_repo.deactivate_user(user_id)
    
    def reactivate_user(self, user_id: int) -> bool:
        """Reactivate user account"""
        return self.user_repo.activate_user(user_id)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user account"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        return self.user_repo.delete(user_id) is not None
    
    def get_active_sessions_count(self, user_id: int) -> int:
        """Get count of active sessions for user"""
        return self.session_repo.get_active_session_count(user_id)
    
    def revoke_session(self, session_id: int, user_id: int) -> bool:
        """Revoke a specific session"""
        session = self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found")
        
        return self.session_repo.invalidate_session(session_id)
    
    def revoke_all_sessions(self, user_id: int) -> int:
        """Revoke all sessions for user"""
        return self.session_repo.revoke_all_sessions(user_id)


# Dependency injection function
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Get user service instance with repositories"""
    return UserService.create_with_repositories(db)
