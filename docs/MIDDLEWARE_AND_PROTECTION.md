# Middleware and Route Protection

## Overview

This document describes the authentication middleware and route protection system implemented for the Oratio platform.

## Architecture

### 1. Next.js Middleware (`frontend/middleware.ts`)

Server-side route protection that runs before pages are rendered.

**Features:**
- Protects routes requiring authentication (`/dashboard`, `/agents`, `/sessions`, `/settings`)
- Redirects unauthenticated users to login with return URL
- Redirects authenticated users away from auth pages (`/login`, `/signup`)
- Runs on all routes except static files and API routes

**Limitations:**
- Currently checks for cookies (not yet implemented)
- For full protection, tokens should be stored in httpOnly cookies instead of localStorage

### 2. API Client with Auto-Authentication (`frontend/lib/api/client.ts`)

Centralized API client that automatically handles authentication.

**Features:**
- Automatic token injection in Authorization header
- Automatic token refresh when expired
- Handles 401 errors and redirects to login
- Type-safe request methods (get, post, put, patch, delete)
- File upload support with authentication

**Usage:**
```typescript
import { get, post } from '@/lib/api/client';

// GET request - token automatically added
const agents = await get<Agent[]>('/api/agents');

// POST request - token automatically added
const newAgent = await post<Agent>('/api/agents/create', {
  agent_name: 'My Agent',
  agent_type: 'voice',
  sop: 'Handle customer inquiries...'
});
```

### 3. Protected Route Component (`frontend/components/auth/protected-route.tsx`)

Client-side route guard component.

**Features:**
- Checks authentication state from AuthContext
- Shows loading state while checking auth
- Redirects to login if not authenticated
- Preserves intended destination URL

**Usage:**
```typescript
import { ProtectedRoute } from '@/components/auth/protected-route';

export default function DashboardLayout({ children }) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  );
}
```

### 4. Dashboard Layout (`frontend/app/dashboard/layout.tsx`)

Example of protected layout implementation.

**Features:**
- Wraps all dashboard routes with ProtectedRoute
- Ensures authentication before rendering any dashboard content

## How It Works

### Authentication Flow

1. **User logs in** → Tokens stored in localStorage
2. **User navigates to protected route** → Middleware checks (currently limited)
3. **ProtectedRoute component checks auth** → Redirects if not authenticated
4. **API calls made** → Client automatically adds token and refreshes if needed
5. **Token expires** → Automatically refreshed using refresh token
6. **Refresh fails** → User redirected to login

### Token Management

**Storage:**
- Access Token: 1 hour validity
- ID Token: 1 hour validity  
- Refresh Token: 30 days validity
- All stored in cookies (secure in production, sameSite: lax)

**Automatic Refresh:**
```typescript
// In API client
if (accessToken && isTokenExpired()) {
  const refreshTokenValue = getRefreshToken();
  if (refreshTokenValue) {
    const tokens = await refreshTokenApi(refreshTokenValue);
    storeTokens(tokens);
    accessToken = tokens.access_token;
  }
}
```

### Error Handling

**401 Unauthorized:**
- Clears all tokens
- Redirects to login page
- Preserves intended destination

**Token Refresh Failure:**
- Clears all tokens
- Shows error message
- Redirects to login

## Implementation Examples

### 1. Protected Page

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

### 2. API Call with Auto-Auth

```typescript
// lib/api/agents.ts
import { get, post } from './client';

export async function getAgents(): Promise<Agent[]> {
  // Token automatically added by client
  return get<Agent[]>('/api/agents');
}

export async function createAgent(data: CreateAgentData): Promise<Agent> {
  // Token automatically added by client
  return post<Agent>('/api/agents/create', data);
}
```

### 3. Using in Components

```typescript
"use client";

import { useState, useEffect } from 'react';
import { getAgents } from '@/lib/api/agents';

export function AgentsList() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadAgents() {
      try {
        const data = await getAgents(); // Auto-authenticated
        setAgents(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    loadAgents();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      {agents.map(agent => (
        <div key={agent.agent_id}>{agent.agent_name}</div>
      ))}
    </div>
  );
}
```

### 4. File Upload with Auth

```typescript
import { uploadFiles } from '@/lib/api/client';

async function handleFileUpload(files: FileList) {
  const formData = new FormData();
  
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  
  try {
    const result = await uploadFiles('/api/agents/upload-kb', formData);
    console.log('Upload successful:', result);
  } catch (error) {
    console.error('Upload failed:', error);
  }
}
```

## Security Considerations

### Current Implementation

✅ **Implemented:**
- JWT token validation on backend
- Automatic token refresh
- 401 error handling
- Client-side route protection
- Token expiry checking
- **Cookie-based token storage** (more secure than localStorage)
- Server-side middleware protection with cookies

⚠️ **Remaining Considerations:**
- Cookies are not httpOnly (set by client, not server)
- No CSRF protection yet

### Production Recommendations

1. **Set Cookies from Backend (httpOnly)**
   ```typescript
   // Backend should set httpOnly cookies on login
   // This prevents JavaScript from accessing tokens (XSS protection)
   response.set_cookie(
       key="oratio_access_token",
       value=access_token,
       httponly=True,
       secure=True,
       samesite="lax"
   )
   ```

2. **Implement CSRF Protection**
   ```typescript
   // Add CSRF tokens for state-changing operations
   ```

3. **Add Rate Limiting**
   ```typescript
   // Limit login attempts and API calls
   ```

4. **Implement Token Rotation**
   ```typescript
   // Rotate refresh tokens on each use
   ```

5. **Add Security Headers**
   ```typescript
   // In next.config.js
   headers: [
     {
       key: 'X-Frame-Options',
       value: 'DENY',
     },
     {
       key: 'X-Content-Type-Options',
       value: 'nosniff',
     },
     // ... more security headers
   ]
   ```

## Testing

### Manual Testing

1. **Test Protected Routes:**
   - Try accessing `/dashboard/agents` without logging in
   - Should redirect to `/login?redirect=/dashboard/agents`

2. **Test Login Redirect:**
   - Log in after being redirected
   - Should return to intended page

3. **Test Token Refresh:**
   - Wait for token to expire (or manually expire it)
   - Make an API call
   - Should automatically refresh and succeed

4. **Test Logout:**
   - Click logout button
   - Should clear tokens and redirect to login
   - Try accessing protected route - should redirect to login

### Automated Testing

```typescript
// Example test
describe('Protected Routes', () => {
  it('redirects to login when not authenticated', () => {
    // Clear tokens
    clearTokens();
    
    // Try to access protected route
    cy.visit('/dashboard/agents');
    
    // Should redirect to login
    cy.url().should('include', '/login');
    cy.url().should('include', 'redirect=/dashboard/agents');
  });
  
  it('allows access when authenticated', () => {
    // Set valid tokens
    storeTokens(mockTokens);
    
    // Access protected route
    cy.visit('/dashboard/agents');
    
    // Should not redirect
    cy.url().should('include', '/dashboard/agents');
  });
});
```

## Troubleshooting

### "Session expired. Please log in again."

**Cause:** Refresh token is invalid or expired

**Solution:** Log in again to get new tokens

### Infinite redirect loop

**Cause:** Middleware and ProtectedRoute both redirecting

**Solution:** Check middleware configuration and ensure routes are properly excluded

### API calls failing with 401

**Cause:** Token not being sent or is invalid

**Solution:** 
- Check token exists in localStorage
- Check token hasn't expired
- Verify backend is accepting the token format

### Token not refreshing automatically

**Cause:** Refresh token missing or API client not being used

**Solution:**
- Ensure all API calls use the `client.ts` functions
- Check refresh token exists in localStorage
- Verify refresh endpoint is working

## Next Steps

1. **Implement Cookie-Based Auth** - Move tokens to httpOnly cookies
2. **Add CSRF Protection** - Implement CSRF tokens
3. **Add Rate Limiting** - Protect against brute force
4. **Add Session Management** - Track active sessions
5. **Add MFA Support** - Two-factor authentication
6. **Add Remember Me** - Longer-lived sessions
7. **Add Activity Logging** - Track user actions

## References

- [Next.js Middleware](https://nextjs.org/docs/app/building-your-application/routing/middleware)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
