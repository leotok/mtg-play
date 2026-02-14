import logging
import sys

# Force basic logging config
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Optional
from datetime import datetime, timedelta

# Configure logger
logger = logging.getLogger(__name__)

# Test logging at module load
logger.info("Auth module loaded - logging test")

from app.core.security import (
    create_access_token, 
    create_refresh_token,
    verify_token,
    validate_email,
    create_password_reset_token,
    verify_password_reset_token
)
from app.core.auth import get_current_user, get_optional_user
from app.services.user_service import get_user_service, UserService
from app.schemas.user import (
    UserCreate, UserLogin, UserUpdate, UserPasswordChange,
    UserResponse, UserProfile, Token, TokenRefresh,
    UserPasswordReset, UserPasswordResetConfirm,
    EmailValidationResponse, UsernameValidationResponse,
    PasswordStrengthResponse, ErrorResponse
)
from app.models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user"""
    logger.info(f"Registration attempt - Email: {user_data.email}, Username: {user_data.username}")
    try:
        user = user_service.create_user(user_data)
        logger.info(f"Registration success - User ID: {user.id}, Email: {user.email}")
        # Convert SQLAlchemy object to Pydantic response
        return UserResponse.from_orm(user)
    except ValueError as e:
        logger.warning(f"Registration failed - ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error - Email: {user_data.email}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """Login user and return tokens"""
    logger.info(f"Login attempt - Email: {user_login.email}")
    try:
        user = user_service.authenticate_user(user_login.email, user_login.password)
        
        if not user:
            logger.warning(f"Login failed - Invalid credentials for email: {user_login.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Login success - User ID: {user.id}, Email: {user.email}")
        
        # Create tokens
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.id}, 
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.id})
        
        logger.debug(f"Tokens created for user {user.id}")
        
        # Create session
        user_service.create_user_session(user.id, refresh_token)
        logger.info(f"User session created - User ID: {user.id}")
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
        
    except ValueError as e:
        logger.warning(f"Login failed - ValueError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error - Email: {user_login.email}, Error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token"""
    try:
        
        # Verify refresh token
        payload = verify_token(token_data.refresh_token, "refresh")
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user session
        session = user_service.get_user_session(token_data.refresh_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session not found or expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user
        user = user_service.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.id}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "refresh_token": token_data.refresh_token,  # Keep same refresh token
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get current user profile with statistics"""
    try:
        stats = user_service.get_user_stats(current_user.id)
        
        # Convert user to response model
        user_response = UserProfile.from_orm(current_user)
        user_response.deck_count = stats.get("deck_count", 0)
        user_response.total_cards = stats.get("total_cards", 0)
        
        return user_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update user profile"""
    try:
        updated_user = user_service.update_user(current_user.id, user_update)
        # Convert SQLAlchemy object to Pydantic response
        return UserResponse.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_change: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Change user password"""
    try:
        success = user_service.change_password(current_user.id, password_change)
        
        if success:
            return {"message": "Password changed successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change failed"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Logout user (invalidate all sessions)"""
    try:
        # Invalidate all sessions for this user
        revoked_count = user_service.revoke_all_sessions(current_user.id)
        
        return {"message": f"Logged out successfully. Revoked {revoked_count} sessions."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email_endpoint(
    email: str,
    user_service: UserService = Depends(get_user_service)
):
    """Validate email format and availability"""
    try:
        # Check availability
        existing_user = user_service.get_user_by_email(email)
        is_valid_format = validate_email(email)
        
        if not is_valid_format:
            return EmailValidationResponse(
                is_valid=False,
                is_available=False,
                message="Invalid email format"
            )
        
        # Check availability
        is_available = existing_user is None
        
        return EmailValidationResponse(
            is_valid=True,
            is_available=is_available,
            message=None if is_available else "Email already registered"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email validation failed"
        )


@router.post("/validate-username", response_model=UsernameValidationResponse)
async def validate_username_endpoint(
    username: str,
    user_service: UserService = Depends(get_user_service)
):
    """Validate username format and availability"""
    try:
        # Check availability
        existing_user = user_service.get_user_by_username(username)
        if len(username) < 3 or len(username) > 50:
            return UsernameValidationResponse(
                is_valid=False,
                is_available=False,
                message="Username must be between 3 and 50 characters"
            )
        
        # Check availability
        is_available = existing_user is None
        
        return UsernameValidationResponse(
            is_valid=True,
            is_available=is_available,
            message=None if is_available else "Username already taken"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Username validation failed"
        )


@router.post("/check-password-strength", response_model=PasswordStrengthResponse)
async def check_password_strength_endpoint(
    password: str
):
    """Check password strength"""
    try:
        from app.core.security import password_validator
        
        result = password_validator.check_strength(password)
        
        return PasswordStrengthResponse(
            is_valid=result["is_valid"],
            strength=result["strength"],
            score=result["score"],
            feedback=result["feedback"],
            suggestions=result["suggestions"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password strength check failed"
        )


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(get_user_service)
):
    """Initiate password reset process"""
    try:
        user = user_service.get_user_by_email(email)
        
        # Always return success to prevent email enumeration
        if user:
            # Create reset token
            reset_token = create_password_reset_token(email)
            
            # TODO: Send email with reset token
            # For now, just log it (in production, use email service)
            print(f"Password reset token for {email}: {reset_token}")
            
            # Store token (you might want to store this in database)
            # For now, we'll just return success
        
        return {"message": "If an account with that email exists, a password reset link has been sent."}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password")
async def reset_password(
    reset_data: UserPasswordResetConfirm,
    user_service: UserService = Depends(get_user_service)
):
    """Reset password with token"""
    try:
        # Verify reset token
        email = verify_password_reset_token(reset_data.token)
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = user_service.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password through user service
        from app.schemas.user import UserPasswordChange
        password_change = UserPasswordChange(
            current_password="",  # Not needed for reset
            new_password=reset_data.new_password
        )
        user_service.change_password(user.id, password_change)
        
        return {"message": "Password has been reset successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Get user's active sessions"""
    try:
        active_sessions_count = user_service.get_active_sessions_count(current_user.id)
        
        return {
            "active_sessions": active_sessions_count,
            "user_id": current_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sessions"
        )


@router.delete("/sessions")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """Revoke all user sessions (force logout everywhere)"""
    try:
        revoked_count = user_service.revoke_all_sessions(current_user.id)
        
        return {"message": f"Revoked {revoked_count} sessions. Please login again."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke sessions"
        )
