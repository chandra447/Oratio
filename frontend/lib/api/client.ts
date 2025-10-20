/**
 * Base API client with automatic authentication token injection.
 * All API calls should use this client to ensure tokens are included.
 */

import { getAccessToken, isTokenExpired, getRefreshToken, storeTokens, clearTokens } from '../auth/token-storage';
import { refreshToken as refreshTokenApi } from './auth';

const getApiBaseUrl = () => {
  if (typeof window !== 'undefined' && window.NEXT_PUBLIC_API_URL) {
    return window.NEXT_PUBLIC_API_URL;
  }
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

export interface ApiError {
  detail: string;
}

/**
 * Make an authenticated API request with automatic token refresh
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Get access token
  let accessToken = getAccessToken();

  // Check if token is expired and refresh if needed
  if (accessToken && isTokenExpired()) {
    const refreshTokenValue = getRefreshToken();

    if (refreshTokenValue) {
      try {
        const tokens = await refreshTokenApi(refreshTokenValue);
        storeTokens(tokens);
        accessToken = tokens.access_token;
      } catch (error) {
        // Refresh failed, clear tokens and throw error
        clearTokens();
        throw new Error('Session expired. Please log in again.');
      }
    } else {
      clearTokens();
      throw new Error('No authentication token found. Please log in.');
    }
  }

  // Add authorization header if token exists
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  // Make the request
  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized - token might be invalid
  if (response.status === 401) {
    clearTokens();

    // Redirect to login if in browser
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }

    throw new Error('Authentication failed. Please log in again.');
  }

  // Handle other errors
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `Request failed with status ${response.status}`
    }));
    throw new Error(error.detail || 'Request failed');
  }

  // Return parsed JSON response
  return response.json();
}

/**
 * Make a GET request
 */
export async function get<T>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'GET' });
}

/**
 * Make a POST request
 */
export async function post<T>(endpoint: string, data?: any): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Make a PUT request
 */
export async function put<T>(endpoint: string, data?: any): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Make a PATCH request
 */
export async function patch<T>(endpoint: string, data?: any): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'PATCH',
    body: data ? JSON.stringify(data) : undefined,
  });
}

/**
 * Make a DELETE request
 */
export async function del<T>(endpoint: string): Promise<T> {
  return apiRequest<T>(endpoint, { method: 'DELETE' });
}

/**
 * Upload files with multipart/form-data
 */
export async function uploadFiles<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  let accessToken = getAccessToken();

  // Check if token is expired and refresh if needed
  if (accessToken && isTokenExpired()) {
    const refreshTokenValue = getRefreshToken();

    if (refreshTokenValue) {
      try {
        const tokens = await refreshTokenApi(refreshTokenValue);
        storeTokens(tokens);
        accessToken = tokens.access_token;
      } catch (error) {
        clearTokens();
        throw new Error('Session expired. Please log in again.');
      }
    }
  }

  const headers: Record<string, string> = {};

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (response.status === 401) {
    clearTokens();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Authentication failed. Please log in again.');
  }

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: `Upload failed with status ${response.status}`
    }));
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}
