"""JWT token validation utilities for AWS Cognito tokens."""

import os
import httpx
from jose import jwt, JWTError
from jose.backends import RSAKey
from typing import Dict, Optional
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


class JWTValidator:
    """Validates JWT tokens from AWS Cognito."""
    
    def __init__(self):
        """Initialize JWT validator with Cognito configuration."""
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = os.getenv('COGNITO_CLIENT_ID')
        
        if not self.user_pool_id or not self.client_id:
            raise ValueError("COGNITO_USER_POOL_ID and COGNITO_CLIENT_ID must be set")
        
        self.jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        self.issuer = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}"
    
    @lru_cache(maxsize=1)
    def get_jwks(self) -> Dict:
        """
        Fetch JSON Web Key Set (JWKS) from Cognito.
        Cached to avoid repeated network calls.
        
        Returns:
            Dict containing JWKS keys
        """
        try:
            response = httpx.get(self.jwks_url, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {e}")
            raise ValueError("Unable to fetch JWKS from Cognito")
    
    def get_signing_key(self, token: str) -> Optional[Dict]:
        """
        Get the signing key for a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict containing RSA key components or None if not found
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            jwks = self.get_jwks()
            
            for key in jwks['keys']:
                if key['kid'] == unverified_header['kid']:
                    return {
                        'kty': key['kty'],
                        'kid': key['kid'],
                        'use': key['use'],
                        'n': key['n'],
                        'e': key['e']
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get signing key: {e}")
            return None
    
    def decode_token(self, token: str, token_use: str = "access") -> Dict:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            token_use: Expected token use ("access" or "id")
            
        Returns:
            Dict containing decoded token payload
            
        Raises:
            ValueError: If token is invalid or verification fails
        """
        try:
            # Get signing key
            rsa_key = self.get_signing_key(token)
            if not rsa_key:
                raise ValueError("Unable to find appropriate signing key")
            
            # Decode and verify token
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=self.client_id if token_use == "id" else None,
                issuer=self.issuer,
                options={
                    "verify_aud": token_use == "id",  # Only verify audience for ID tokens
                    "verify_exp": True,
                    "verify_iss": True
                }
            )
            
            # Verify token_use claim
            if payload.get('token_use') != token_use:
                raise ValueError(f"Token is not an {token_use} token")
            
            return payload
            
        except JWTError as e:
            logger.error(f"JWT validation failed: {e}")
            raise ValueError(f"Invalid JWT token: {str(e)}")
        except Exception as e:
            logger.error(f"Token decode failed: {e}")
            raise ValueError(f"Token validation error: {str(e)}")
    
    def decode_access_token(self, token: str) -> Dict:
        """
        Decode and validate an access token.
        
        Args:
            token: Access token string
            
        Returns:
            Dict containing decoded token payload with user information
        """
        return self.decode_token(token, token_use="access")
    
    def decode_id_token(self, token: str) -> Dict:
        """
        Decode and validate an ID token.
        
        Args:
            token: ID token string
            
        Returns:
            Dict containing decoded token payload with user profile
        """
        return self.decode_token(token, token_use="id")
    
    def get_user_id_from_token(self, token: str) -> str:
        """
        Extract user ID (sub) from token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID (Cognito sub)
            
        Raises:
            ValueError: If token is invalid or sub claim is missing
        """
        try:
            payload = self.decode_access_token(token)
            user_id = payload.get('sub')
            
            if not user_id:
                raise ValueError("Token does not contain sub claim")
            
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to extract user ID from token: {e}")
            raise
    
    def get_user_email_from_token(self, token: str) -> Optional[str]:
        """
        Extract user email from ID token.
        
        Args:
            token: ID token string
            
        Returns:
            User email or None if not present
        """
        try:
            payload = self.decode_id_token(token)
            return payload.get('email')
        except Exception as e:
            logger.error(f"Failed to extract email from token: {e}")
            return None


# Global JWT validator instance
jwt_validator = JWTValidator()
