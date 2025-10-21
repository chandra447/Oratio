/**
 * Centralized API configuration that handles runtime URL injection
 */

/**
 * Get the API base URL from runtime config or build-time environment variable.
 * This function checks multiple sources in order of precedence:
 * 1. Runtime config injected by docker-entrypoint.sh (window.NEXT_PUBLIC_API_URL)
 * 2. Build-time environment variable (process.env.NEXT_PUBLIC_API_URL)
 * 3. Fallback to localhost for local development
 */
export function getApiBaseUrl(): string {
  // Check for runtime config first (injected by docker-entrypoint.sh in production)
  if (typeof window !== 'undefined' && (window as any).NEXT_PUBLIC_API_URL) {
    const runtimeUrl = (window as any).NEXT_PUBLIC_API_URL;
    // Don't use placeholder value
    if (runtimeUrl !== '__PLACEHOLDER__') {
      return runtimeUrl;
    }
  }
  
  // Fallback to build-time environment variable or localhost for dev
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

