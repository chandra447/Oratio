"""API Key models"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class APIKeyPermission(str, Enum):
    """API Key permissions"""

    CHAT = "chat"
    VOICE = "voice"
    ADMIN = "admin"


class APIKeyStatus(str, Enum):
    """API Key status"""

    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class APIKey(BaseModel):
    """API Key model"""

    model_config = ConfigDict(populate_by_name=True, by_alias=False)

    api_key_hash: str = Field(..., alias="apiKeyHash", description="SHA-256 hash of the API key")
    user_id: str = Field(..., alias="userId", description="User ID who owns this key")
    agent_id: str = Field(..., alias="agentId", description="Agent ID this key is for")
    key_name: str = Field(..., alias="keyName", description="Human-readable name for the key")
    permissions: List[APIKeyPermission] = Field(
        default=[APIKeyPermission.CHAT], description="Permissions granted to this key"
    )
    status: APIKeyStatus = Field(default=APIKeyStatus.ACTIVE, description="Key status")
    rate_limit: int = Field(default=1000, alias="rateLimit", description="Requests per hour")
    created_at: int = Field(..., alias="createdAt", description="Creation timestamp")
    expires_at: Optional[int] = Field(None, alias="expiresAt", description="Expiration timestamp")
    last_used_at: Optional[int] = Field(None, alias="lastUsedAt", description="Last usage timestamp")


class APIKeyCreate(BaseModel):
    """API Key creation request"""

    agent_id: str = Field(..., description="Agent ID to create key for")
    key_name: str = Field(..., description="Human-readable name for the key")
    permissions: List[APIKeyPermission] = Field(
        default=[APIKeyPermission.CHAT], description="Permissions to grant"
    )
    rate_limit: int = Field(default=1000, description="Requests per hour")
    expires_in_days: Optional[int] = Field(None, description="Days until expiration")


class APIKeyResponse(BaseModel):
    """API Key response (includes plain key only on creation)"""

    model_config = ConfigDict(populate_by_name=True, by_alias=False)

    api_key_hash: str = Field(..., alias="apiKeyHash")
    user_id: str = Field(..., alias="userId")
    agent_id: str = Field(..., alias="agentId")
    key_name: str = Field(..., alias="keyName")
    permissions: List[APIKeyPermission]
    status: APIKeyStatus
    rate_limit: int = Field(..., alias="rateLimit")
    created_at: int = Field(..., alias="createdAt")
    expires_at: Optional[int] = Field(None, alias="expiresAt")
    # Only included on creation
    api_key: Optional[str] = Field(None, alias="apiKey", description="Plain API key (only shown once)")


class APIKeyValidation(BaseModel):
    """API Key validation result"""

    valid: bool
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    permissions: List[APIKeyPermission] = []
    reason: Optional[str] = None  # Reason if invalid
