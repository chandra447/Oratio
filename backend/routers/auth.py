"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Annotated
import logging

from models.user import (
    UserCreate,
    UserLogin,
    UserConfirm,
    TokenResponse,
    TokenRefresh,
    UserProfile
)
from services.auth_service import auth_service
from dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **name**: User's full name
    
    Returns user_id and confirmation status.
    Email verification required before login.
    """
    try:
        result = await auth_service.register_user(user_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )


@router.post("/confirm")
async def confirm_registration(confirm_data: UserConfirm):
    """
    Confirm user email with verification code.
    
    - **email**: User email address
    - **confirmation_code**: 6-digit code from email
    
    Returns success status.
    """
    try:
        await auth_service.confirm_registration(confirm_data.email, confirm_data.confirmation_code)
        return {"message": "Email confirmed successfully. You can now log in."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Confirmation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Confirmation failed. Please try again later."
        )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """
    Authenticate user and get JWT tokens.
    
    - **email**: User email address
    - **password**: User password
    
    Returns access_token, id_token, and refresh_token.
    """
    try:
        tokens = await auth_service.login_user(login_data)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh):
    """
    Refresh access and ID tokens using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access_token and id_token.
    """
    try:
        tokens = await auth_service.refresh_tokens(token_data.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again later."
        )


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: Annotated[UserProfile, Depends(get_current_user)]):
    """
    Get current user profile.
    
    Requires valid access token in Authorization header.
    Returns user profile information.
    """
    return current_user


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: Annotated[UserProfile, Depends(get_current_user)]
):
    """
    Change user password.
    
    - **current_password**: Current password
    - **new_password**: New password (minimum 8 characters)
    
    Requires valid access token.
    """
    try:
        # Note: We need the access token, not just the user profile
        # This is a simplified version - in production, pass the token through
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Password change endpoint needs access token implementation"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/forgot-password")
async def forgot_password(email: str):
    """
    Initiate forgot password flow.
    
    - **email**: User email address
    
    Sends verification code to email.
    Returns success even if email doesn't exist (security best practice).
    """
    try:
        await auth_service.forgot_password(email)
        return {
            "message": "If an account exists with this email, you will receive a password reset code."
        }
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        # Don't reveal errors to prevent user enumeration
        return {
            "message": "If an account exists with this email, you will receive a password reset code."
        }


@router.post("/reset-password")
async def reset_password(email: str, confirmation_code: str, new_password: str):
    """
    Reset password with confirmation code.
    
    - **email**: User email address
    - **confirmation_code**: 6-digit code from email
    - **new_password**: New password (minimum 8 characters)
    
    Returns success status.
    """
    try:
        await auth_service.reset_password(email, confirmation_code, new_password)
        return {"message": "Password reset successfully. You can now log in with your new password."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed. Please try again later."
        )


@router.post("/logout")
async def logout(current_user: Annotated[UserProfile, Depends(get_current_user)]):
    """
    Logout user (client-side token removal).
    
    Note: Cognito tokens cannot be invalidated server-side.
    Client must remove tokens from storage.
    """
    return {"message": "Logged out successfully. Please remove tokens from client storage."}
