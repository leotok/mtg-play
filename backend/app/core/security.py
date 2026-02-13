import httpx
import asyncio
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from fastapi import HTTPException, status
import re
from app.core.config import settings

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def _prehash_password(password: str) -> bytes:
    """Pre-hash password with SHA-256 to handle bcrypt's 72-byte limit.
    
    This ensures consistent behavior across all bcrypt versions and
    avoids passlib compatibility issues with bcrypt 4.1+.
    """
    return hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')


def get_password_hash(password: str) -> str:
    """Hash a password with bcrypt, using SHA-256 pre-hashing for compatibility."""
    prehashed = _prehash_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(prehashed, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    prehashed = _prehash_password(plain_password)
    return bcrypt.checkpw(prehashed, hashed_password.encode('utf-8'))


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    # Convert user_id to string for JWT compliance
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token (7 days expiration)"""
    to_encode = data.copy()
    # Convert user_id to string for JWT compliance
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])
    
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type if specified
        if token_type == "refresh" and payload.get("type") != "refresh":
            return None
        elif token_type == "access" and payload.get("type") == "refresh":
            return None
        
        # Convert sub back to integer if it's a string
        if "sub" in payload and isinstance(payload["sub"], str):
            try:
                payload["sub"] = int(payload["sub"])
            except ValueError:
                pass  # Keep as string if conversion fails
        
        return payload
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create password reset token (1 hour expiration)"""
    to_encode = {"email": email, "type": "password_reset"}
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "password_reset":
            return None
            
        return payload.get("email")
    except JWTError:
        return None


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    import secrets
    return secrets.token_urlsafe(length)


class PasswordValidator:
    """Enhanced password validation with detailed feedback"""
    
    @staticmethod
    def check_strength(password: str) -> dict:
        """Comprehensive password strength check"""
        result = {
            "is_valid": True,
            "score": 0,
            "feedback": [],
            "suggestions": []
        }
        
        # Length check
        if len(password) < 8:
            result["is_valid"] = False
            result["feedback"].append("Password is too short (minimum 8 characters)")
        elif len(password) >= 12:
            result["score"] += 2
        else:
            result["score"] += 1
        
        # Uppercase check
        if re.search(r'[A-Z]', password):
            result["score"] += 1
        else:
            result["is_valid"] = False
            result["feedback"].append("Password needs at least one uppercase letter")
        
        # Lowercase check
        if re.search(r'[a-z]', password):
            result["score"] += 1
        else:
            result["is_valid"] = False
            result["feedback"].append("Password needs at least one lowercase letter")
        
        # Number check
        if re.search(r'\d', password):
            result["score"] += 1
        else:
            result["is_valid"] = False
            result["feedback"].append("Password needs at least one number")
        
        # Special character check
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result["score"] += 1
        else:
            result["is_valid"] = False
            result["feedback"].append("Password needs at least one special character")
        
        # Common patterns check
        common_patterns = [
            r'123', r'password', r'qwerty', r'abc123', r'admin'
        ]
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                result["score"] -= 1
                result["suggestions"].append("Avoid common patterns")
        
        # Repetitive characters check
        if re.search(r'(.)\1{2,}', password):
            result["score"] -= 1
            result["suggestions"].append("Avoid repetitive characters")
        
        # Strength rating
        if result["score"] >= 5:
            result["strength"] = "Strong"
        elif result["score"] >= 3:
            result["strength"] = "Medium"
        else:
            result["strength"] = "Weak"
        
        return result


class TokenManager:
    """Enhanced token management with blacklisting support"""
    
    def __init__(self):
        self.blacklisted_tokens = set()  # In production, use Redis or database
    
    def blacklist_token(self, token: str):
        """Add token to blacklist"""
        self.blacklisted_tokens.add(token)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in self.blacklisted_tokens
    
    def cleanup_expired_tokens(self):
        """Clean up expired tokens from blacklist (placeholder)"""
        # In production, implement proper cleanup logic
        pass


# Global instances
password_validator = PasswordValidator()
token_manager = TokenManager()
