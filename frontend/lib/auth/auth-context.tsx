"use client";

/**
 * Authentication context for managing user authentication state.
 * Provides login, logout, and user profile management across the application.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import type { UserProfile, LoginData, RegisterData } from '../api/auth';
import * as authApi from '../api/auth';
import * as tokenStorage from './token-storage';
import { waitForRuntimeConfig } from '../api/runtime-config';

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginData) => Promise<void>;
  register: (data: RegisterData) => Promise<{ message: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  // Load user profile on mount
  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = useCallback(async () => {
    try {
      // Wait for runtime configuration to be available
      await waitForRuntimeConfig();
      
      const accessToken = tokenStorage.getAccessToken();
      
      if (!accessToken || tokenStorage.isTokenExpired()) {
        // Try to refresh token
        const refreshToken = tokenStorage.getRefreshToken();
        if (refreshToken) {
          try {
            const tokens = await authApi.refreshToken(refreshToken);
            tokenStorage.storeTokens(tokens);
            
            // Load user with new token
            const userProfile = await authApi.getCurrentUser(tokens.access_token);
            setUser(userProfile);
          } catch (error) {
            // Refresh failed, clear tokens
            tokenStorage.clearTokens();
            setUser(null);
          }
        } else {
          setUser(null);
        }
      } else {
        // Load user with existing token
        const userProfile = await authApi.getCurrentUser(accessToken);
        setUser(userProfile);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (data: LoginData) => {
    try {
      // Wait for runtime configuration to be available
      await waitForRuntimeConfig();
      
      const tokens = await authApi.login(data);
      tokenStorage.storeTokens(tokens);
      
      // Load user profile
      const userProfile = await authApi.getCurrentUser(tokens.access_token);
      setUser(userProfile);
      
      // Check for redirect URL in query params
      const urlParams = new URLSearchParams(window.location.search);
      const redirectUrl = urlParams.get('redirect') || '/dashboard/agents';
      
      // Redirect to intended page or dashboard
      router.push(redirectUrl);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }, [router]);

  const register = useCallback(async (data: RegisterData): Promise<{ message: string }> => {
    try {
      // Wait for runtime configuration to be available
      await waitForRuntimeConfig();
      
      const result = await authApi.register(data);
      return {
        message: result.message || 'Registration successful. Please check your email for verification code.'
      };
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      const accessToken = tokenStorage.getAccessToken();
      if (accessToken) {
        await authApi.logout(accessToken);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      tokenStorage.clearTokens();
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  const refreshUser = useCallback(async () => {
    await loadUser();
  }, [loadUser]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
