"""Shared dependencies for FastAPI application."""

from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from utils.jwt_utils import jwt_validator
from services.auth_service import AuthService
from services.agent_service import AgentService
from services.knowledge_base_service import KnowledgeBaseService
from services.s3_service import S3Service
from services.api_key_service import APIKeyService
from services.agent_invocation_service import AgentInvocationService
from aws.cognito_client import CognitoClient
from aws.dynamodb_client import DynamoDBClient
from aws.s3_client import S3Client
from aws.stepfunctions_client import StepFunctionsClient
from models.user import UserProfile
from config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


# Dependency injection functions
def get_cognito_client() -> CognitoClient:
    """
    Get CognitoClient instance.
    Can be overridden for testing.
    """
    return CognitoClient()


def get_auth_service(
    cognito_client: Annotated[CognitoClient, Depends(get_cognito_client)]
) -> AuthService:
    """
    Get AuthService instance with injected dependencies.
    Can be overridden for testing.
    """
    return AuthService(cognito_client=cognito_client)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> UserProfile:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Injected AuthService instance
        
    Returns:
        UserProfile of authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        token = credentials.credentials
        
        # Validate token and get user profile
        user_profile = await auth_service.get_current_user(token)
        
        return user_profile
        
    except ValueError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    current_user: Annotated[UserProfile, Depends(get_current_user)]
) -> str:
    """
    Extract user ID from current user.
    
    Args:
        current_user: Current authenticated user profile
        
    Returns:
        User ID string
    """
    return current_user.user_id


async def get_current_user_optional(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(HTTPBearer(auto_error=False))
    ],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> Optional[UserProfile]:
    """
    Dependency to get current user if token is provided (optional authentication).
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        auth_service: Injected AuthService instance
        
    Returns:
        UserProfile if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_profile = await auth_service.get_current_user(token)
        return user_profile
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None


def get_user_id_from_token(token: str) -> str:
    """
    Extract user ID from JWT token.
    
    Args:
        token: JWT access token
        
    Returns:
        User ID (Cognito sub)
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        return jwt_validator.get_user_id_from_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# Service dependencies
def get_dynamodb_client() -> DynamoDBClient:
    """Get DynamoDBClient instance"""
    return DynamoDBClient()


def get_agent_service(
    dynamodb_client: Annotated[DynamoDBClient, Depends(get_dynamodb_client)]
) -> AgentService:
    """Get AgentService instance"""
    return AgentService(
        dynamodb_client=dynamodb_client,
        table_name=settings.AGENTS_TABLE
    )


def get_api_key_service(
    dynamodb_client: Annotated[DynamoDBClient, Depends(get_dynamodb_client)]
) -> APIKeyService:
    """Get APIKeyService instance"""
    return APIKeyService(
        dynamodb_client=dynamodb_client,
        table_name=settings.API_KEYS_TABLE
    )


def get_agent_invocation_service() -> AgentInvocationService:
    """Get AgentInvocationService instance"""
    return AgentInvocationService(region=settings.BEDROCK_REGION)
