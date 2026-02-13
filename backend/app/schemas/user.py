from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    is_active: bool = Field(True, description="Whether the user is active")


class UserCreate(UserBase):
    """User registration schema"""
    password: str = Field(..., description="User password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """User profile update schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="User email address")
    is_active: Optional[bool] = Field(None, description="Whether the user is active")
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower() if v else v


class UserPasswordChange(BaseModel):
    """Password change schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserPasswordReset(BaseModel):
    """Password reset schema"""
    email: EmailStr = Field(..., description="User email address")


class UserPasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Confirm new password")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
        

class UserResponse(UserBase):
    """User response schema"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    email_verified: bool
    
    class Config:
        from_attributes = True


class UserProfile(UserResponse):
    """Extended user profile schema"""
    deck_count: Optional[int] = Field(0, description="Number of decks owned by user")
    total_cards: Optional[int] = Field(0, description="Total cards across all decks")
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


class TokenData(BaseModel):
    """Token data schema"""
    user_id: Optional[int] = None
    exp: Optional[int] = None


class UserStats(BaseModel):
    """User statistics schema"""
    deck_count: int
    total_cards: int
    unique_cards: int
    avg_deck_size: float
    favorite_colors: list[str]
    recent_activity: list[dict]


class UserActivity(BaseModel):
    """User activity schema"""
    action: str
    resource_type: str
    resource_id: int
    timestamp: datetime
    details: Optional[dict] = None


class UserPreferences(BaseModel):
    """User preferences schema"""
    theme: str = "light"
    language: str = "en"
    notifications_enabled: bool = True
    public_profile: bool = False
    favorite_colors: list[str] = []
    
    class Config:
        from_attributes = True


# Validation schemas for requests
class EmailValidation(BaseModel):
    """Email validation schema"""
    email: EmailStr = Field(..., description="Email address to validate")


class UsernameValidation(BaseModel):
    """Username validation schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username to validate")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()


class PasswordStrengthCheck(BaseModel):
    """Password strength check schema"""
    password: str = Field(..., description="Password to check strength")
    
    @validator('password')
    def validate_password_format(cls, v):
        if len(v) < 1:
            raise ValueError('Password cannot be empty')
        return v


# Response schemas for validation
class EmailValidationResponse(BaseModel):
    """Email validation response"""
    is_valid: bool
    is_available: bool
    message: Optional[str] = None


class UsernameValidationResponse(BaseModel):
    """Username validation response"""
    is_valid: bool
    is_available: bool
    message: Optional[str] = None


class PasswordStrengthResponse(BaseModel):
    """Password strength response"""
    is_valid: bool
    strength: str
    score: int
    feedback: list[str]
    suggestions: list[str]


# Session management schemas
class UserSession(BaseModel):
    """User session schema"""
    id: int
    user_id: int
    refresh_token: str
    expires_at: datetime
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    """Session creation schema"""
    user_id: int
    refresh_token: str
    expires_at: datetime


class SessionResponse(BaseModel):
    """Session response schema"""
    id: int
    user_id: int
    expires_at: datetime
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# Error response schemas
class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationError(BaseModel):
    """Validation error response"""
    detail: list[dict]
    error_code: str = "validation_error"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
