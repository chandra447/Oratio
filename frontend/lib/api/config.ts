/**
 * Centralized API configuration using NEXT_PUBLIC_ENV
 */

/**
 * Get the API base URL based on NEXT_PUBLIC_ENV environment variable
 */
export function getApiBaseUrl(): string {
  const env = process.env.NEXT_PUBLIC_ENV || 'local';
  
  switch (env) {
    case 'aws':
      return 'https://d3cp7cujulcncl.cloudfront.net';
    case 'local':
    default:
      return 'http://localhost:8000';
  }
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
