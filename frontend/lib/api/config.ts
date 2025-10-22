/**
 * Centralized API configuration that handles runtime URL injection
 */

import { isRuntimeConfigAvailable } from './runtime-config';

/**
 * Validates if a URL is properly formatted
 */
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Get the API base URL from runtime config.
 * This function ONLY reads from window.NEXT_PUBLIC_API_URL to avoid Next.js build-time inlining.
 *
 * For client-side code:
 * 1. Runtime config injected by docker-entrypoint.sh (window.NEXT_PUBLIC_API_URL)
 * 2. Fallback to localhost for local development
 *
 * For server-side code (SSR):
 * 1. Build-time environment variable (process.env.NEXT_PUBLIC_API_URL)
 * 2. Fallback to localhost for local development
 */
export function getApiBaseUrl(): string {
  // Client-side: Only use runtime config from window
  if (typeof window !== 'undefined') {
    if (isRuntimeConfigAvailable()) {
      const runtimeUrl = (window as any).NEXT_PUBLIC_API_URL;
      if (runtimeUrl && runtimeUrl !== '__PLACEHOLDER__' && isValidUrl(runtimeUrl)) {
        return runtimeUrl;
      }
      
      if (!isValidUrl(runtimeUrl)) {
        console.warn(`Invalid runtime API URL: ${runtimeUrl}. Using fallback.`);
      }
    }
    
    // Client-side fallback to localhost for development
    const fallbackUrl = 'http://localhost:8000';
    console.warn(`Runtime API URL not available or invalid. Using fallback: ${fallbackUrl}`);
    return fallbackUrl;
  }
  
  // Server-side: Use build-time environment variable (only runs on server)
  const buildTimeUrl = process.env.NEXT_PUBLIC_API_URL;
  if (buildTimeUrl && isValidUrl(buildTimeUrl)) {
    return buildTimeUrl;
  }
  
  // Server-side fallback
  const fallbackUrl = 'http://localhost:8000';
  if (!buildTimeUrl) {
    console.warn(`No API URL configured for SSR. Using fallback: ${fallbackUrl}`);
  } else {
    console.warn(`Invalid build-time API URL: ${buildTimeUrl}. Using fallback: ${fallbackUrl}`);
  }
  
  return fallbackUrl;
}

/**
 * Get the API base URL with validation and error handling
 * Throws an error if no valid URL can be determined
 */
export function getValidatedApiBaseUrl(): string {
  const url = getApiBaseUrl();
  
  if (!isValidUrl(url)) {
    throw new Error(`Invalid API URL configuration: ${url}`);
  }
  
  return url;
}
