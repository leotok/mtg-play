from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import JWTError, jwt

from app.core.security import SECRET_KEY, ALGORITHM, verify_token, token_manager
from app.core.database import get_db
from app.repositories import UserRepository, DeckRepository
from app.repositories.dependencies import get_user_repository, get_deck_repository
from app.models.user import User

# HTTP Bearer scheme for token extraction
security = HTTPBearer()

# Optional user dependency (for public endpoints)
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Optional[User]:
    """Get user from token if provided, otherwise return None"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        # Check if token is blacklisted
        if token_manager.is_token_blacklisted(token):
            return None
        
        # Verify token
        payload = verify_token(token)
        if payload is None:
            return None
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user = user_repo.get_by_id(user_id)
        return user if user and user.is_active else None
        
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """Get current authenticated user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Check if token is blacklisted
        if token_manager.is_token_blacklisted(token):
            raise credentials_exception
        
        # Verify token
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        # Get user ID from token
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (additional validation if needed)"""
    return current_user


def check_deck_ownership(deck_id: int, user_id: int, deck_repo) -> bool:
    """Check if user owns the deck"""
    deck = deck_repo.get_by_id(deck_id)
    return deck is not None and deck.owner_id == user_id


def require_deck_ownership():
    """Decorator to require deck ownership"""
    def dependency(deck_id: int, current_user: User = Depends(get_current_user), deck_repo: DeckRepository = Depends(get_deck_repository)):
        deck = deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        if deck.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this deck"
            )
        
        return current_user
    return dependency


def require_deck_ownership_or_public():
    """Decorator to require deck ownership or public access"""
    def dependency(deck_id: int, current_user: User = Depends(get_current_user), deck_repo: DeckRepository = Depends(get_deck_repository)):
        deck = deck_repo.get_by_id(deck_id)
        if not deck:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        
        # Allow access if user owns the deck or deck is public
        if deck.owner_id != current_user.id and not deck.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: This deck is private"
            )
        
        return current_user
    return dependency


class OwnershipValidator:
    """Helper class for ownership validation"""
    
    @staticmethod
    def validate_deck_ownership(deck_id: int, user_id: int, deck_repo) -> bool:
        """Validate deck ownership"""
        return check_deck_ownership(deck_id, user_id, deck_repo)
    
    @staticmethod
    def validate_user_resource(resource_user_id: int, current_user_id: int) -> bool:
        """Validate user resource ownership"""
        return resource_user_id == current_user_id
    
    @staticmethod
    def require_ownership_or_raise(resource_id: int, resource_type: str, user_id: int, deck_repo):
        """Require ownership or raise HTTP exception"""
        if resource_type == "deck":
            if not check_deck_ownership(resource_id, user_id, deck_repo):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: You don't own this {resource_type}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown resource type: {resource_type}"
            )


# Convenience functions for common ownership checks
def get_user_deck_or_404(deck_id: int, current_user: User = Depends(get_current_user), deck_repo: DeckRepository = Depends(get_deck_repository)):
    """Get deck if user owns it, otherwise raise 404/403"""
    deck = deck_repo.get_by_id(deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    if deck.owner_id != current_user.id and not deck.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this deck"
        )
    
    return deck


def get_public_deck_or_404(deck_id: int, current_user: Optional[User] = Depends(get_optional_user), deck_repo: DeckRepository = Depends(get_deck_repository)):
    """Get deck if public or owned by user, otherwise raise 404/403"""
    deck = deck_repo.get_by_id(deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    # Allow access if deck is public or user owns it
    if not deck.is_public and (not current_user or deck.owner_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: This deck is private"
        )
    
    return deck


# Rate limiting helper for auth endpoints
class AuthRateLimiter:
    """Simple in-memory rate limiter for auth endpoints"""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.attempts = {}  # In production, use Redis
    
    def is_rate_limited(self, identifier: str) -> bool:
        """Check if identifier is rate limited"""
        import time
        
        now = time.time()
        window_start = now - (self.window_minutes * 60)
        
        # Clean old attempts
        if identifier in self.attempts:
            self.attempts[identifier] = [
                attempt_time for attempt_time in self.attempts[identifier]
                if attempt_time > window_start
            ]
        else:
            self.attempts[identifier] = []
        
        # Check if exceeded limit
        if len(self.attempts[identifier]) >= self.max_attempts:
            return True
        
        # Record this attempt
        self.attempts[identifier].append(now)
        return False


# Global rate limiter instances
login_rate_limiter = AuthRateLimiter(max_attempts=5, window_minutes=15)
register_rate_limiter = AuthRateLimiter(max_attempts=3, window_minutes=60)
