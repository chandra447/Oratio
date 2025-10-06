/**
 * Token storage utilities for managing JWT tokens in browser storage.
 * Uses localStorage for persistence across sessions.
 */

import type { TokenResponse } from '../api/auth';

const ACCESS_TOKEN_KEY = 'oratio_access_token';
const ID_TOKEN_KEY = 'oratio_id_token';
const REFRESH_TOKEN_KEY = 'oratio_refresh_token';
const TOKEN_EXPIRY_KEY = 'oratio_token_expiry';

/**
 * Store authentication tokens in localStorage
 */
export function storeTokens(tokens: TokenResponse): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(ID_TOKEN_KEY, tokens.id_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    
    // Calculate expiry timestamp
    const expiryTime = Date.now() + (tokens.expires_in * 1000);
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
  } catch (error) {
    console.error('Failed to store tokens:', error);
  }
}

/**
 * Get access token from localStorage
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;

  try {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    console.error('Failed to get access token:', error);
    return null;
  }
}

/**
 * Get ID token from localStorage
 */
export function getIdToken(): string | null {
  if (typeof window === 'undefined') return null;

  try {
    return localStorage.getItem(ID_TOKEN_KEY);
  } catch (error) {
    console.error('Failed to get ID token:', error);
    return null;
  }
}

/**
 * Get refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;

  try {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  } catch (error) {
    console.error('Failed to get refresh token:', error);
    return null;
  }
}

/**
 * Check if access token is expired
 */
export function isTokenExpired(): boolean {
  if (typeof window === 'undefined') return true;

  try {
    const expiryTime = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!expiryTime) return true;

    return Date.now() >= parseInt(expiryTime, 10);
  } catch (error) {
    console.error('Failed to check token expiry:', error);
    return true;
  }
}

/**
 * Check if user is authenticated (has valid tokens)
 */
export function isAuthenticated(): boolean {
  const accessToken = getAccessToken();
  const refreshToken = getRefreshToken();
  
  return !!(accessToken && refreshToken && !isTokenExpired());
}

/**
 * Clear all authentication tokens from localStorage
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return;

  try {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(ID_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  } catch (error) {
    console.error('Failed to clear tokens:', error);
  }
}

/**
 * Get all tokens as an object
 */
export function getAllTokens(): {
  accessToken: string | null;
  idToken: string | null;
  refreshToken: string | null;
} {
  return {
    accessToken: getAccessToken(),
    idToken: getIdToken(),
    refreshToken: getRefreshToken(),
  };
}
