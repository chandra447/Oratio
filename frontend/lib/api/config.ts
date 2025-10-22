/**
 * Centralized API configuration
 * Uses NEXT_PUBLIC_API_URL environment variable set at build time
 * Falls back to localhost for local development
 */

/**
 * Get the API base URL from environment variable or default to localhost
 */
export function getApiBaseUrl(): string {
  // NEXT_PUBLIC_API_URL is set at build time via Docker build args
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  
  // For local development, default to localhost
  if (!apiUrl) {
    return 'http://localhost:8000';
  }
  
  return apiUrl;
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
