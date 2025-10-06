# Authentication Implementation - localStorage Based

## Overview

This document describes the **actual implemented authentication system** for Oratio platform using **localStorage** for token storage.

## Architecture: Simple & Pragmatic

### Token Storage: localStorage

**Why localStorage?**
- ✅ Simple to implement and debug
- ✅ Works immediately without backend complexity
- ✅ No CORS complications
- ✅ Visible in DevTools for easy debugging
- ✅ Perfect for MVP

**Location:** `frontend/lib/auth/token-storage.ts`

### Protection Layers

1. **Client-Side Route Guard** - `ProtectedRoute` component
2. **API Client with Auto-Auth** - Automatic token injection
3. **Backend JWT Validation** - Cognito JWKS validation

## File Structure

```
frontend/
├── lib/
│   ├── auth/
│   │   ├── token-storage.ts      # localStorage token management
│   │   └── auth-context.tsx      # Global auth state
│   └── api/
│       ├── client.ts              # Auto-authenticated API client
│       └── auth.ts                # Auth API endpoints
├── components/
│   └── auth/
│       └── protected-route.tsx    # Client-side route guard
└── middleware.ts                  # Basic middleware (no auth check)

backend/
├── routers/
│   └── auth.py                    # Auth endpoints (returns tokens)
├── services/
│   └── auth_service.py            # Auth business logic
├── aws/
│   └── cognito_client.py          # Cognito wrapper
└── utils/
    └── jwt_utils.py               # JWT validation
```

## How It Works

### 1. User Registration

```typescript
// Frontend
const { register } = useAuth();
await register({
  email: 'user@example.com',
  password: 'SecurePass123!',
  name: 'John Doe'
});
```

**Flow:**
1. POST `/api/auth/register`
2. Backend creates user in Cognito
3. Backend creates user profile in DynamoDB
4. Cognito sends verification email
5. User must verify email before login

### 2. User Login

```typescript
// Frontend
const { login } = useAuth();
await login({
  email: 'user@example.com',
  password: 'SecurePass123!'
});
```

**Flow:**
1. POST `/api/auth/login`
2. Backend authenticates with Cognito
3. Backend returns JWT tokens:
   ```json
   {
     "access_token": "eyJ...",
     "id_token": "eyJ...",
     "refresh_token": "eyJ...",
     "token_type": "Bearer",
     "expires_in": 3600
   }
   ```
4. Frontend stores tokens in localStorage
5. Frontend loads user profile
6. Redirects to dashboard

### 3. Protected API Calls

```typescript
// Anywhere in your app
import { get } from '@/lib/api/client';

// Token automatically added!
const agents = await get('/api/agents');
```

**Flow:**
1. Client checks if token exists
2. Client checks if token is expired
3. If expired, automatically refreshes using refresh token
4. Adds `Authorization: Bearer {token}` header
5. Makes request
6. If 401, clears tokens and redirects to login

### 4. Token Refresh

**Automatic** - happens transparently when token expires:

```typescript
// In client.ts
if (accessToken && isTokenExpired()) {
  const refreshTokenValue = getRefreshToken();
  if (refreshTokenValue) {
    const tokens = await refreshTokenApi(refreshTokenValue);
    storeTokens(tokens);
    accessToken = tokens.access_token;
  }
}
```

### 5. Logout

```typescript
const { logout } = useAuth();
await logout();
```

**Flow:**
1. Calls backend logout endpoint (optional)
2. Clears all tokens from localStorage
3. Clears user state
4. Redirects to login

## API Endpoints

### Backend (FastAPI)

```python
# Registration
POST /api/auth/register
Body: { email, password, name }
Returns: { user_id, email, message }

# Email Confirmation
POST /api/auth/confirm
Body: { email, confirmation_code }
Returns: { message }

# Login
POST /api/auth/login
Body: { email, password }
Returns: { access_token, id_token, refresh_token, token_type, expires_in }

# Refresh Token
POST /api/auth/refresh
Body: { refresh_token }
Returns: { access_token, id_token, refresh_token, token_type, expires_in }

# Get Current User
GET /api/auth/me
Headers: Authorization: Bearer {access_token}
Returns: { user_id, email, name, subscription_tier, created_at, last_login }

# Logout
POST /api/auth/logout
Headers: Authorization: Bearer {access_token}
Returns: { message }

# Forgot Password
POST /api/auth/forgot-password
Body: { email }
Returns: { message }

# Reset Password
POST /api/auth/reset-password
Body: { email, confirmation_code, new_password }
Returns: { message }
```

## Token Management

### Token Storage (localStorage)

```typescript
// Store tokens after login
storeTokens({
  access_token: "...",
  id_token: "...",
  refresh_token: "...",
  token_type: "Bearer",
  expires_in: 3600
});

// Get access token
const token = getAccessToken();

// Check if expired
const expired = isTokenExpired();

// Check if authenticated
const authenticated = isAuthenticated();

// Clear all tokens
clearTokens();
```

### Token Lifecycle

- **Access Token**: 1 hour validity
- **ID Token**: 1 hour validity
- **Refresh Token**: 30 days validity
- **Auto-refresh**: Happens automatically when access token expires

## Usage Examples

### Protected Page

```typescript
// app/dashboard/agents/page.tsx
"use client";

import { useAuth } from '@/lib/auth/auth-context';

export default function AgentsPage() {
  const { user, logout } = useAuth();
  
  return (
    <div>
      <h1>Welcome, {user?.name}!</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### Protected Layout

```typescript
// app/dashboard/layout.tsx
"use client";

import { ProtectedRoute } from '@/components/auth/protected-route';

export default function DashboardLayout({ children }) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  );
}
```

### API Call

```typescript
// lib/api/agents.ts
import { get, post } from './client';

export async function getAgents() {
  // Token automatically added
  return get<Agent[]>('/api/agents');
}

export async function createAgent(data: CreateAgentData) {
  // Token automatically added
  return post<Agent>('/api/agents/create', data);
}
```

### Using in Component

```typescript
"use client";

import { useState, useEffect } from 'react';
import { getAgents } from '@/lib/api/agents';

export function AgentsList() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getAgents(); // Auto-authenticated!
        setAgents(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div>Loading...</div>;
  return <div>{/* Render agents */}</div>;
}
```

## Security Features

### Current Implementation

✅ **JWT Validation** - All tokens validated against Cognito JWKS  
✅ **HTTPS in Production** - Tokens encrypted in transit  
✅ **Short-lived Tokens** - Access tokens expire in 1 hour  
✅ **Automatic Refresh** - Seamless token renewal  
✅ **Tenant Isolation** - userId from JWT enforces data boundaries  
✅ **Token Expiry Tracking** - Prevents use of expired tokens  

### Limitations

⚠️ **XSS Vulnerability** - If attacker injects script, can steal tokens from localStorage  
⚠️ **No Server-Side Route Protection** - Middleware can't check localStorage  

### Mitigation Strategies

1. **Content Security Policy (CSP)**
   ```typescript
   // next.config.ts
   headers: [
     {
       key: 'Content-Security-Policy',
       value: "default-src 'self'; script-src 'self'"
     }
   ]
   ```

2. **Input Sanitization** - Always sanitize user inputs
3. **Regular Security Audits** - Monitor for vulnerabilities
4. **HTTPS Only** - Never use HTTP in production

## Testing

### Manual Testing Checklist

- [ ] Register new user
- [ ] Verify email (check Cognito console)
- [ ] Login with credentials
- [ ] Check tokens in localStorage (DevTools → Application → Local Storage)
- [ ] Access protected route `/dashboard/agents`
- [ ] Make API call (check Network tab for Authorization header)
- [ ] Wait for token to expire (or manually delete)
- [ ] Make another API call (should auto-refresh)
- [ ] Logout
- [ ] Try accessing protected route (should redirect to login)

### Testing with curl

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#",
    "name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'

# Get current user (replace TOKEN)
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer TOKEN"
```

## Environment Variables

### Backend (.env)

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# Cognito
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id
COGNITO_REGION=us-east-1

# DynamoDB
USERS_TABLE=oratio-users
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment Checklist

### Before Deploying

- [ ] Deploy Cognito User Pool via CDK
- [ ] Deploy DynamoDB users table via CDK
- [ ] Update backend .env with Cognito credentials
- [ ] Update frontend .env.local with API URL
- [ ] Test registration flow
- [ ] Test login flow
- [ ] Test protected routes
- [ ] Test API calls
- [ ] Test logout

### After Deploying

- [ ] Verify HTTPS is enabled
- [ ] Check Cognito email verification works
- [ ] Test token refresh
- [ ] Monitor CloudWatch logs
- [ ] Test from different browsers

## Troubleshooting

### "No authentication token found"

**Cause:** Tokens not in localStorage  
**Solution:** Log in again

### "Session expired. Please log in again"

**Cause:** Refresh token expired or invalid  
**Solution:** Log in again

### "Invalid JWT token"

**Cause:** Token malformed or Cognito validation failed  
**Solution:** Clear localStorage and log in again

### Tokens not persisting

**Cause:** localStorage disabled or private browsing  
**Solution:** Enable localStorage or use regular browsing mode

### CORS errors

**Cause:** Backend not allowing frontend origin  
**Solution:** Check CORS configuration in backend

## Future Enhancements (Optional)

If you need maximum security later, consider:

1. **HttpOnly Cookies** - Backend sets cookies, JavaScript can't access
2. **CSRF Tokens** - Additional protection for state-changing operations
3. **Token Rotation** - Rotate refresh tokens on each use
4. **MFA** - Two-factor authentication
5. **Session Management** - Track active sessions
6. **Rate Limiting** - Prevent brute force attacks

## Summary

✅ **Simple** - localStorage + client-side protection  
✅ **Secure Enough** - JWT validation, HTTPS, short-lived tokens  
✅ **Works Now** - No backend changes needed  
✅ **Debuggable** - Easy to see tokens in DevTools  
✅ **Upgradeable** - Can add cookies later if needed  

**This is a solid, pragmatic authentication system perfect for MVP!** 🚀
