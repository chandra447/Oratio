"""API Key management service"""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from aws.dynamodb_client import DynamoDBClient
from models.api_key import (
    APIKey,
    APIKeyCreate,
    APIKeyPermission,
    APIKeyResponse,
    APIKeyStatus,
    APIKeyValidation,
)

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys"""

    def __init__(self, dynamodb_client: DynamoDBClient, table_name: str = "oratio-api-keys"):
        self.dynamodb = dynamodb_client
        self.table_name = table_name

    def _hash_key(self, api_key: str) -> str:
        """Hash an API key using SHA-256"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def _generate_key(self) -> str:
        """Generate a secure random API key"""
        return f"oratio_{secrets.token_urlsafe(32)}"

    def create_api_key(
        self, user_id: str, key_data: APIKeyCreate
    ) -> Optional[APIKeyResponse]:
        """
        Create a new API key

        Args:
            user_id: User ID creating the key
            key_data: API key creation data

        Returns:
            Optional[APIKeyResponse]: Created key with plain key (only shown once)
        """
        try:
            # Generate plain key
            plain_key = self._generate_key()
            key_hash = self._hash_key(plain_key)

            # Calculate expiration
            expires_at = None
            if key_data.expires_in_days:
                expires_at = int(
                    (datetime.now() + timedelta(days=key_data.expires_in_days)).timestamp()
                )

            # Create API key object
            api_key = APIKey(
                api_key_hash=key_hash,
                user_id=user_id,
                agent_id=key_data.agent_id,
                key_name=key_data.key_name,
                permissions=key_data.permissions,
                status=APIKeyStatus.ACTIVE,
                rate_limit=key_data.rate_limit,
                created_at=int(datetime.now().timestamp()),
                expires_at=expires_at,
            )

            # Store in DynamoDB (use camelCase aliases)
            item = api_key.model_dump(by_alias=True)
            success = self.dynamodb.put_item(self.table_name, item)

            if success:
                logger.info(f"Created API key for agent {key_data.agent_id}")
                return APIKeyResponse(
                    **api_key.model_dump(),
                    api_key=plain_key,  # Include plain key only on creation
                )
            else:
                logger.error("Failed to create API key in DynamoDB")
                return None

        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return None

    def validate_api_key(
        self, api_key: str, required_permission: Optional[APIKeyPermission] = None
    ) -> APIKeyValidation:
        """
        Validate an API key

        Args:
            api_key: Plain API key to validate
            required_permission: Optional permission to check

        Returns:
            APIKeyValidation: Validation result
        """
        try:
            # Hash the provided key
            key_hash = self._hash_key(api_key)

            # Look up in DynamoDB
            item = self.dynamodb.get_item(
                self.table_name, key={"apiKeyHash": key_hash}
            )

            if not item:
                return APIKeyValidation(valid=False, reason="API key not found")

            api_key_obj = APIKey(**item)

            # Check status
            if api_key_obj.status != APIKeyStatus.ACTIVE:
                return APIKeyValidation(
                    valid=False, reason=f"API key is {api_key_obj.status.value}"
                )

            # Check expiration
            if api_key_obj.expires_at:
                if datetime.now().timestamp() > api_key_obj.expires_at:
                    # Update status to expired
                    self._update_key_status(key_hash, APIKeyStatus.EXPIRED)
                    return APIKeyValidation(valid=False, reason="API key expired")

            # Check permission if required
            if required_permission:
                if required_permission not in api_key_obj.permissions:
                    return APIKeyValidation(
                        valid=False,
                        reason=f"API key does not have {required_permission.value} permission",
                    )

            # Update last used timestamp
            self._update_last_used(key_hash)

            # Valid!
            return APIKeyValidation(
                valid=True,
                user_id=api_key_obj.user_id,
                agent_id=api_key_obj.agent_id,
                permissions=api_key_obj.permissions,
            )

        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return APIKeyValidation(valid=False, reason="Internal error")

    def validate_key_for_agent(self, api_key: str, agent_id: str) -> APIKeyValidation:
        """
        Validate that an API key belongs to a specific agent

        Args:
            api_key: Plain API key
            agent_id: Agent ID to validate against

        Returns:
            APIKeyValidation: Validation result
        """
        validation = self.validate_api_key(api_key)

        if not validation.valid:
            return validation

        # Check if key belongs to this agent
        if validation.agent_id != agent_id:
            return APIKeyValidation(
                valid=False,
                reason=f"API key does not belong to agent {agent_id}",
            )

        return validation

    def list_user_keys(self, user_id: str, agent_id: Optional[str] = None) -> List[APIKey]:
        """
        List all API keys for a user

        Args:
            user_id: User ID
            agent_id: Optional agent ID filter

        Returns:
            List[APIKey]: List of API keys (without plain keys)
        """
        try:
            # Query by userId using GSI
            items = self.dynamodb.query_by_gsi(
                table_name=self.table_name,
                index_name="userId-agentId-index",
                partition_key_name="userId",
                partition_key_value=user_id,
            )

            keys = [APIKey(**item) for item in items]

            # Filter by agent_id if provided
            if agent_id:
                keys = [k for k in keys if k.agent_id == agent_id]

            return keys

        except Exception as e:
            logger.error(f"Error listing API keys for user {user_id}: {e}")
            return []

    def revoke_api_key(self, user_id: str, key_hash: str) -> bool:
        """
        Revoke an API key

        Args:
            user_id: User ID (for authorization)
            key_hash: API key hash to revoke

        Returns:
            bool: True if successful
        """
        try:
            # Verify ownership
            item = self.dynamodb.get_item(
                self.table_name, key={"apiKeyHash": key_hash}
            )

            if not item:
                logger.warning(f"API key not found: {key_hash}")
                return False

            if item.get("userId") != user_id:
                logger.warning(f"User {user_id} attempted to revoke key owned by {item.get('userId')}")
                return False

            # Update status
            return self._update_key_status(key_hash, APIKeyStatus.REVOKED)

        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            return False

    def _update_key_status(self, key_hash: str, status: APIKeyStatus) -> bool:
        """Update API key status"""
        try:
            updates = {
                "status": status.value,
            }

            return self.dynamodb.update_item(
                table_name=self.table_name,
                key={"apiKeyHash": key_hash},
                updates=updates,
            )

        except Exception as e:
            logger.error(f"Error updating key status: {e}")
            return False

    def _update_last_used(self, key_hash: str) -> bool:
        """Update last used timestamp"""
        try:
            updates = {
                "lastUsedAt": int(datetime.now().timestamp()),
            }

            return self.dynamodb.update_item(
                table_name=self.table_name,
                key={"apiKeyHash": key_hash},
                updates=updates,
            )

        except Exception as e:
            logger.error(f"Error updating last used: {e}")
            return False
