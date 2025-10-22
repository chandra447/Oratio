/**
 * Centralized API configuration - hardcoded to production URL
 */

/**
 * Get the API base URL - always returns the production URL
 */
export function getApiBaseUrl(): string {
  return 'https://d3cp7cujulcncl.cloudfront.net';
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
