from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """
    Validate JWT token and return current user.
    This is a placeholder - will be implemented with Cognito integration.
    """
    token = credentials.credentials
    # TODO: Implement JWT validation with Cognito
    # For now, return a mock user
    return {"user_id": "mock-user-id", "email": "user@example.com"}


async def get_current_user_id(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> str:
    """Extract user ID from current user"""
    return current_user["user_id"]
