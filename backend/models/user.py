"""User data models for authentication and profile management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user model with common fields."""
    
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Model for user registration."""
    
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Model for user login."""
    
    email: EmailStr
    password: str


class User(UserBase):
    """Complete user model with all fields."""
    
    user_id: str
    created_at: int
    last_login: Optional[int] = None
    subscription_tier: str = "free"
    cognito_sub: str  # Cognito user sub identifier
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """JWT token response model."""
    
    access_token: str
    id_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class TokenRefresh(BaseModel):
    """Model for token refresh request."""
    
    refresh_token: str


class UserProfile(BaseModel):
    """User profile information."""
    
    user_id: str
    email: str
    name: str
    subscription_tier: str
    created_at: int
    last_login: Optional[int] = None
