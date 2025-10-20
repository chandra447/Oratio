"""API Keys router"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from models.api_key import APIKey, APIKeyCreate, APIKeyResponse
from models.user import UserProfile
from services.api_key_service import APIKeyService
from dependencies import get_api_key_service, get_current_user

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=APIKeyResponse, response_model_by_alias=False, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: UserProfile = Depends(get_current_user),
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    """
    Create a new API key
    
    The API key will only be shown once upon creation.
    Store it securely as it cannot be retrieved later.
    """
    api_key = api_key_service.create_api_key(current_user.user_id, key_data)
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )
    
    return api_key


@router.get("", response_model=List[APIKey], response_model_by_alias=False)
async def list_api_keys(
    agent_id: str = None,
    current_user: UserProfile = Depends(get_current_user),
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    """
    List all API keys for the current user
    
    Optionally filter by agent_id
    """
    keys = api_key_service.list_user_keys(current_user.user_id, agent_id)
    return keys


@router.delete("/{key_hash}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_hash: str,
    current_user: UserProfile = Depends(get_current_user),
    api_key_service: APIKeyService = Depends(get_api_key_service),
):
    """
    Revoke an API key
    
    This will immediately invalidate the key.
    """
    success = api_key_service.revoke_api_key(current_user.user_id, key_hash)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or already revoked",
        )
    
    return None

