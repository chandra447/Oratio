"""Authentication service for user registration, login, and token management."""

import os
import boto3
from datetime import datetime
from typing import Optional, Dict, Any
import logging
from botocore.exceptions import ClientError

from aws.cognito_client import CognitoClient
from models.user import User, UserCreate, UserLogin, TokenResponse, UserProfile
from utils.jwt_utils import jwt_validator

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(
        self,
        cognito_client: Optional[CognitoClient] = None,
        dynamodb_resource: Optional[Any] = None,
        users_table_name: Optional[str] = None
    ):
        """
        Initialize authentication service with AWS clients.
        
        Args:
            cognito_client: Optional CognitoClient instance (for testing/DI)
            dynamodb_resource: Optional boto3 DynamoDB resource (for testing/DI)
            users_table_name: Optional users table name (defaults to env var)
        """
        self.cognito_client = cognito_client or CognitoClient()
        self.dynamodb = dynamodb_resource or boto3.resource('dynamodb')
        table_name = users_table_name or os.getenv('USERS_TABLE', 'oratio-users')
        self.users_table = self.dynamodb.Table(table_name)
    
    async def register_user(self, user_data: UserCreate) -> Dict:
        """
        Register a new user in Cognito and DynamoDB.
        
        Args:
            user_data: User registration data
            
        Returns:
            Dict containing user_id and registration status
            
        Raises:
            ValueError: If registration fails
        """
        try:
            # Register user in Cognito
            cognito_response = self.cognito_client.sign_up(
                email=user_data.email,
                password=user_data.password,
                name=user_data.name
            )
            
            user_sub = cognito_response['user_sub']
            current_timestamp = int(datetime.utcnow().timestamp())
            
            # Create user profile in DynamoDB
            user_item = {
                'userId': user_sub,
                'email': user_data.email,
                'name': user_data.name,
                'cognitoSub': user_sub,
                'subscriptionTier': 'free',
                'createdAt': current_timestamp,
                'lastLogin': None
            }
            
            self.users_table.put_item(Item=user_item)
            
            logger.info(f"User registered successfully: {user_data.email}")
            
            return {
                'user_id': user_sub,
                'email': user_data.email,
                'user_confirmed': cognito_response['user_confirmed'],
                'message': 'User registered successfully. Please check your email for verification code.'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'UsernameExistsException':
                raise ValueError("User with this email already exists")
            elif error_code == 'InvalidPasswordException':
                raise ValueError("Password does not meet requirements")
            elif error_code == 'InvalidParameterException':
                raise ValueError(f"Invalid parameter: {error_message}")
            else:
                logger.error(f"Registration failed: {error_code} - {error_message}")
                raise ValueError(f"Registration failed: {error_message}")
    
    async def confirm_registration(self, email: str, confirmation_code: str) -> bool:
        """
        Confirm user email with verification code.
        
        Args:
            email: User email address
            confirmation_code: Verification code from email
            
        Returns:
            True if confirmation successful
            
        Raises:
            ValueError: If confirmation fails
        """
        try:
            self.cognito_client.confirm_sign_up(email, confirmation_code)
            logger.info(f"User confirmed: {email}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'CodeMismatchException':
                raise ValueError("Invalid verification code")
            elif error_code == 'ExpiredCodeException':
                raise ValueError("Verification code has expired")
            else:
                logger.error(f"Confirmation failed: {error_code} - {error_message}")
                raise ValueError(f"Confirmation failed: {error_message}")
    
    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        """
        Authenticate user and return JWT tokens.
        
        Args:
            login_data: User login credentials
            
        Returns:
            TokenResponse containing JWT tokens
            
        Raises:
            ValueError: If authentication fails
        """
        try:
            # Authenticate with Cognito
            auth_response = self.cognito_client.initiate_auth(
                email=login_data.email,
                password=login_data.password
            )
            
            # Extract user ID from ID token
            id_token_payload = jwt_validator.decode_id_token(auth_response['id_token'])
            user_sub = id_token_payload['sub']
            
            # Update last login timestamp in DynamoDB
            current_timestamp = int(datetime.utcnow().timestamp())
            self.users_table.update_item(
                Key={'userId': user_sub},
                UpdateExpression='SET lastLogin = :timestamp',
                ExpressionAttributeValues={':timestamp': current_timestamp}
            )
            
            logger.info(f"User logged in: {login_data.email}")
            
            return TokenResponse(**auth_response)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                raise ValueError("Invalid email or password")
            elif error_code == 'UserNotConfirmedException':
                raise ValueError("Email not verified. Please check your email for verification code.")
            elif error_code == 'UserNotFoundException':
                raise ValueError("Invalid email or password")
            else:
                logger.error(f"Login failed: {error_code} - {error_message}")
                raise ValueError(f"Login failed: {error_message}")
    
    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access and ID tokens using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            TokenResponse with new tokens
            
        Raises:
            ValueError: If token refresh fails
        """
        try:
            auth_response = self.cognito_client.refresh_token(refresh_token)
            
            # Note: refresh token is not returned in refresh response
            auth_response['refresh_token'] = refresh_token
            
            logger.info("Tokens refreshed successfully")
            return TokenResponse(**auth_response)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                raise ValueError("Invalid or expired refresh token")
            else:
                logger.error(f"Token refresh failed: {error_code} - {error_message}")
                raise ValueError(f"Token refresh failed: {error_message}")
    
    async def get_current_user(self, access_token: str) -> UserProfile:
        """
        Get current user profile from access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            UserProfile with user information
            
        Raises:
            ValueError: If token is invalid or user not found
        """
        try:
            # Validate token and extract user ID
            user_id = jwt_validator.get_user_id_from_token(access_token)
            
            # Get user profile from DynamoDB
            response = self.users_table.get_item(Key={'userId': user_id})
            
            if 'Item' not in response:
                raise ValueError("User not found")
            
            user_item = response['Item']
            
            return UserProfile(
                user_id=user_item['userId'],
                email=user_item['email'],
                name=user_item['name'],
                subscription_tier=user_item.get('subscriptionTier', 'free'),
                created_at=user_item['createdAt'],
                last_login=user_item.get('lastLogin')
            )
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            raise ValueError("Failed to retrieve user profile")
    
    async def change_password(
        self,
        access_token: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            access_token: Valid access token
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            ValueError: If password change fails
        """
        try:
            self.cognito_client.change_password(
                access_token=access_token,
                previous_password=current_password,
                proposed_password=new_password
            )
            
            logger.info("Password changed successfully")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'NotAuthorizedException':
                raise ValueError("Current password is incorrect")
            elif error_code == 'InvalidPasswordException':
                raise ValueError("New password does not meet requirements")
            else:
                logger.error(f"Password change failed: {error_code} - {error_message}")
                raise ValueError(f"Password change failed: {error_message}")
    
    async def forgot_password(self, email: str) -> bool:
        """
        Initiate forgot password flow.
        
        Args:
            email: User email address
            
        Returns:
            True if forgot password initiated successfully
        """
        try:
            self.cognito_client.forgot_password(email)
            logger.info(f"Forgot password initiated for: {email}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'UserNotFoundException':
                # Don't reveal if user exists
                logger.info(f"Forgot password requested for non-existent user: {email}")
                return True
            else:
                logger.error(f"Forgot password failed: {e}")
                raise ValueError("Failed to initiate password reset")
    
    async def reset_password(
        self,
        email: str,
        confirmation_code: str,
        new_password: str
    ) -> bool:
        """
        Reset password with confirmation code.
        
        Args:
            email: User email address
            confirmation_code: Verification code from email
            new_password: New password
            
        Returns:
            True if password reset successful
            
        Raises:
            ValueError: If password reset fails
        """
        try:
            self.cognito_client.confirm_forgot_password(
                email=email,
                confirmation_code=confirmation_code,
                new_password=new_password
            )
            
            logger.info(f"Password reset successfully for: {email}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'CodeMismatchException':
                raise ValueError("Invalid verification code")
            elif error_code == 'ExpiredCodeException':
                raise ValueError("Verification code has expired")
            elif error_code == 'InvalidPasswordException':
                raise ValueError("Password does not meet requirements")
            else:
                logger.error(f"Password reset failed: {error_code} - {error_message}")
                raise ValueError(f"Password reset failed: {error_message}")


# Global auth service instance
auth_service = AuthService()
