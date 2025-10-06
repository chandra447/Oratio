"""AWS Cognito client wrapper for user authentication operations."""

import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class CognitoClient:
    """Wrapper for AWS Cognito operations."""
    
    def __init__(
        self,
        cognito_client: Optional[Any] = None,
        user_pool_id: Optional[str] = None,
        client_id: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize Cognito client with configuration.
        
        Args:
            cognito_client: Optional boto3 cognito-idp client (for testing/DI)
            user_pool_id: Cognito User Pool ID (defaults to env var)
            client_id: Cognito Client ID (defaults to env var)
            region: AWS region (defaults to env var)
        """
        self.client = cognito_client or boto3.client(
            'cognito-idp',
            region_name=region or os.getenv('AWS_REGION', 'us-east-1')
        )
        self.user_pool_id = user_pool_id or os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = client_id or os.getenv('COGNITO_CLIENT_ID')
        
        if not self.user_pool_id or not self.client_id:
            raise ValueError("COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID must be set")
    
    def sign_up(self, email: str, password: str, name: str) -> Dict:
        """
        Register a new user in Cognito.
        
        Args:
            email: User email address
            password: User password
            name: User full name
            
        Returns:
            Dict containing user_sub and other registration details
            
        Raises:
            ClientError: If registration fails
        """
        try:
            response = self.client.sign_up(
                ClientId=self.client_id,
                Username=email,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'name', 'Value': name}
                ]
            )
            
            logger.info(f"User registered successfully: {email}")
            return {
                'user_sub': response['UserSub'],
                'user_confirmed': response.get('UserConfirmed', False)
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Cognito sign up failed: {error_code} - {e}")
            raise
    
    def confirm_sign_up(self, email: str, confirmation_code: str) -> bool:
        """
        Confirm user email with verification code.
        
        Args:
            email: User email address
            confirmation_code: Verification code sent to email
            
        Returns:
            True if confirmation successful
            
        Raises:
            ClientError: If confirmation fails
        """
        try:
            self.client.confirm_sign_up(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=confirmation_code
            )
            logger.info(f"User confirmed successfully: {email}")
            return True
            
        except ClientError as e:
            logger.error(f"Cognito confirmation failed: {e}")
            raise
    
    def initiate_auth(self, email: str, password: str) -> Dict:
        """
        Authenticate user and get JWT tokens.
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            Dict containing access_token, id_token, refresh_token, and expires_in
            
        Raises:
            ClientError: If authentication fails
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                }
            )
            
            auth_result = response['AuthenticationResult']
            logger.info(f"User authenticated successfully: {email}")
            
            return {
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'refresh_token': auth_result['RefreshToken'],
                'expires_in': auth_result['ExpiresIn'],
                'token_type': 'Bearer'
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Cognito authentication failed: {error_code} - {e}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Refresh access and ID tokens using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict containing new access_token, id_token, and expires_in
            
        Raises:
            ClientError: If token refresh fails
        """
        try:
            response = self.client.initiate_auth(
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            auth_result = response['AuthenticationResult']
            logger.info("Token refreshed successfully")
            
            return {
                'access_token': auth_result['AccessToken'],
                'id_token': auth_result['IdToken'],
                'expires_in': auth_result['ExpiresIn'],
                'token_type': 'Bearer'
            }
            
        except ClientError as e:
            logger.error(f"Token refresh failed: {e}")
            raise
    
    def get_user(self, access_token: str) -> Dict:
        """
        Get user information from access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            Dict containing user attributes
            
        Raises:
            ClientError: If user retrieval fails
        """
        try:
            response = self.client.get_user(AccessToken=access_token)
            
            # Convert attributes list to dict
            attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            return {
                'username': response['Username'],
                'attributes': attributes
            }
            
        except ClientError as e:
            logger.error(f"Get user failed: {e}")
            raise
    
    def admin_get_user(self, email: str) -> Optional[Dict]:
        """
        Get user information by email (admin operation).
        
        Args:
            email: User email address
            
        Returns:
            Dict containing user information or None if not found
        """
        try:
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=email
            )
            
            # Convert attributes list to dict
            attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            return {
                'username': response['Username'],
                'user_status': response['UserStatus'],
                'enabled': response['Enabled'],
                'attributes': attributes,
                'user_create_date': response['UserCreateDate'],
                'user_last_modified_date': response['UserLastModifiedDate']
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'UserNotFoundException':
                return None
            logger.error(f"Admin get user failed: {e}")
            raise
    
    def change_password(self, access_token: str, previous_password: str, proposed_password: str) -> bool:
        """
        Change user password.
        
        Args:
            access_token: Valid access token
            previous_password: Current password
            proposed_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            ClientError: If password change fails
        """
        try:
            self.client.change_password(
                AccessToken=access_token,
                PreviousPassword=previous_password,
                ProposedPassword=proposed_password
            )
            logger.info("Password changed successfully")
            return True
            
        except ClientError as e:
            logger.error(f"Password change failed: {e}")
            raise
    
    def forgot_password(self, email: str) -> bool:
        """
        Initiate forgot password flow.
        
        Args:
            email: User email address
            
        Returns:
            True if forgot password initiated successfully
            
        Raises:
            ClientError: If forgot password fails
        """
        try:
            self.client.forgot_password(
                ClientId=self.client_id,
                Username=email
            )
            logger.info(f"Forgot password initiated for: {email}")
            return True
            
        except ClientError as e:
            logger.error(f"Forgot password failed: {e}")
            raise
    
    def confirm_forgot_password(self, email: str, confirmation_code: str, new_password: str) -> bool:
        """
        Confirm forgot password with code and set new password.
        
        Args:
            email: User email address
            confirmation_code: Verification code sent to email
            new_password: New password
            
        Returns:
            True if password reset successful
            
        Raises:
            ClientError: If password reset fails
        """
        try:
            self.client.confirm_forgot_password(
                ClientId=self.client_id,
                Username=email,
                ConfirmationCode=confirmation_code,
                Password=new_password
            )
            logger.info(f"Password reset successfully for: {email}")
            return True
            
        except ClientError as e:
            logger.error(f"Password reset failed: {e}")
            raise
