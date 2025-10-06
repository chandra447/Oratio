# Dependency Injection Pattern

## Overview

The Oratio backend uses dependency injection (DI) to improve testability, flexibility, and maintainability. This document explains the DI pattern used in the authentication system.

## Why Dependency Injection?

### Benefits

1. **Testability**: Easy to mock dependencies in unit tests
2. **Flexibility**: Can swap implementations without changing code
3. **Loose Coupling**: Components don't directly instantiate their dependencies
4. **Configuration**: Easy to configure different environments (dev, test, prod)
5. **SOLID Principles**: Follows Dependency Inversion Principle

### Before DI (Tightly Coupled)

```python
class CognitoClient:
    def __init__(self):
        # Directly instantiates boto3 client - hard to test
        self.client = boto3.client('cognito-idp')
```

### After DI (Loosely Coupled)

```python
class CognitoClient:
    def __init__(self, cognito_client=None):
        # Accepts injected client - easy to test with mocks
        self.client = cognito_client or boto3.client('cognito-idp')
```

## Implementation

### 1. CognitoClient with DI

**File**: `backend/aws/cognito_client.py`

```python
class CognitoClient:
    def __init__(
        self,
        cognito_client: Optional[Any] = None,
        user_pool_id: Optional[str] = None,
        client_id: Optional[str] = None,
        region: Optional[str] = None
    ):
        """
        Initialize with optional dependencies.
        Falls back to environment variables if not provided.
        """
        self.client = cognito_client or boto3.client(
            'cognito-idp',
            region_name=region or os.getenv('AWS_REGION', 'us-east-1')
        )
        self.user_pool_id = user_pool_id or os.getenv('COGNITO_USER_POOL_ID')
        self.client_id = client_id or os.getenv('COGNITO_CLIENT_ID')
```

**Benefits**:
- Can inject mock boto3 client for testing
- Can override configuration for different environments
- Still works with defaults for production

### 2. AuthService with DI

**File**: `backend/services/auth_service.py`

```python
class AuthService:
    def __init__(
        self,
        cognito_client: Optional[CognitoClient] = None,
        dynamodb_resource: Optional[Any] = None,
        users_table_name: Optional[str] = None
    ):
        """
        Initialize with optional dependencies.
        Falls back to creating instances if not provided.
        """
        self.cognito_client = cognito_client or CognitoClient()
        self.dynamodb = dynamodb_resource or boto3.resource('dynamodb')
        table_name = users_table_name or os.getenv('USERS_TABLE', 'oratio-users')
        self.users_table = self.dynamodb.Table(table_name)
```

**Benefits**:
- Can inject mock CognitoClient for testing
- Can inject mock DynamoDB resource for testing
- Can override table name for different environments

### 3. FastAPI Dependency Functions

**File**: `backend/dependencies.py`

```python
def get_cognito_client() -> CognitoClient:
    """
    Factory function for CognitoClient.
    Can be overridden in tests using app.dependency_overrides.
    """
    return CognitoClient()


def get_auth_service(
    cognito_client: Annotated[CognitoClient, Depends(get_cognito_client)]
) -> AuthService:
    """
    Factory function for AuthService with injected CognitoClient.
    Can be overridden in tests using app.dependency_overrides.
    """
    return AuthService(cognito_client=cognito_client)
```

**Benefits**:
- FastAPI automatically handles dependency resolution
- Easy to override for testing
- Clear dependency graph

### 4. Using Dependencies in Routes

**File**: `backend/routers/auth.py`

```python
@router.post("/register")
async def register(
    user_data: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    AuthService is automatically injected by FastAPI.
    """
    result = await auth_service.register_user(user_data)
    return result
```

**Benefits**:
- No global instances
- Each request gets fresh dependencies
- Easy to test individual routes

## Testing with DI

### Unit Testing Services

```python
import pytest
from unittest.mock import Mock, AsyncMock
from backend.services.auth_service import AuthService
from backend.aws.cognito_client import CognitoClient

def test_register_user():
    # Create mock dependencies
    mock_cognito = Mock(spec=CognitoClient)
    mock_cognito.sign_up = Mock(return_value={'user_sub': 'test-123'})
    
    mock_dynamodb = Mock()
    mock_table = Mock()
    mock_dynamodb.Table = Mock(return_value=mock_table)
    
    # Inject mocks into service
    auth_service = AuthService(
        cognito_client=mock_cognito,
        dynamodb_resource=mock_dynamodb,
        users_table_name='test-users'
    )
    
    # Test the service
    result = await auth_service.register_user(user_data)
    
    # Verify mocks were called correctly
    mock_cognito.sign_up.assert_called_once()
    mock_table.put_item.assert_called_once()
```

### Integration Testing Routes

```python
from fastapi.testclient import TestClient
from backend.main import app
from backend.dependencies import get_auth_service

def test_register_endpoint():
    # Create mock auth service
    mock_auth_service = Mock(spec=AuthService)
    mock_auth_service.register_user = AsyncMock(
        return_value={'user_id': 'test-123', 'message': 'Success'}
    )
    
    # Override dependency
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    
    # Test the endpoint
    client = TestClient(app)
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'Test123!@#',
        'name': 'Test User'
    })
    
    assert response.status_code == 201
    assert response.json()['user_id'] == 'test-123'
    
    # Clean up
    app.dependency_overrides.clear()
```

## Dependency Graph

```
Route Handler
    ↓ (depends on)
get_auth_service()
    ↓ (depends on)
get_cognito_client()
    ↓ (creates)
CognitoClient
    ↓ (uses)
boto3.client('cognito-idp')
```

## Best Practices

### 1. Optional Dependencies with Defaults

```python
def __init__(self, client: Optional[Client] = None):
    self.client = client or create_default_client()
```

**Why**: Works in production without configuration, but testable with mocks.

### 2. Factory Functions for FastAPI

```python
def get_service() -> Service:
    return Service()
```

**Why**: FastAPI can override these for testing.

### 3. Type Hints

```python
def __init__(self, client: Optional[boto3.Client] = None):
```

**Why**: Better IDE support and type checking.

### 4. Environment Variable Fallbacks

```python
user_pool_id = user_pool_id or os.getenv('COGNITO_USER_POOL_ID')
```

**Why**: Configuration from environment in production, explicit in tests.

## Configuration for Different Environments

### Development

```python
# Uses environment variables from .env
auth_service = AuthService()  # Defaults to env vars
```

### Testing

```python
# Uses mocks
auth_service = AuthService(
    cognito_client=mock_cognito,
    dynamodb_resource=mock_dynamodb
)
```

### Production

```python
# Uses environment variables from deployment
auth_service = AuthService()  # Defaults to env vars
```

## Common Patterns

### 1. Service Layer Pattern

```python
# Service depends on clients
class AuthService:
    def __init__(self, cognito_client, dynamodb_resource):
        self.cognito = cognito_client
        self.db = dynamodb_resource
```

### 2. Repository Pattern

```python
# Repository depends on database
class UserRepository:
    def __init__(self, dynamodb_resource, table_name):
        self.table = dynamodb_resource.Table(table_name)
```

### 3. Client Wrapper Pattern

```python
# Wrapper depends on AWS client
class CognitoClient:
    def __init__(self, cognito_client):
        self.client = cognito_client
```

## Migration Guide

### Converting Existing Code to DI

**Before**:
```python
class MyService:
    def __init__(self):
        self.client = boto3.client('s3')
```

**After**:
```python
class MyService:
    def __init__(self, s3_client=None):
        self.client = s3_client or boto3.client('s3')
```

**Steps**:
1. Add optional parameter to `__init__`
2. Use parameter if provided, else create default
3. Create factory function in `dependencies.py`
4. Update route handlers to use `Depends()`

## References

- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Dependency Inversion Principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [Testing with Mocks](https://docs.python.org/3/library/unittest.mock.html)
