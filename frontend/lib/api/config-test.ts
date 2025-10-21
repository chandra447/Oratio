/**
 * Simple test to verify API configuration works correctly
 * This file can be used in development to test the configuration
 */

import { getApiBaseUrl } from './config';
import { isRuntimeConfigAvailable } from './runtime-config';

/**
 * Test function to verify API configuration
 * Call this function in the browser console to test: window.testApiConfig()
 */
export function testApiConfig() {
  console.log('=== API Configuration Test ===');
  
  // Check if we're in browser
  console.log('Browser environment:', typeof window !== 'undefined');
  
  // Check runtime config availability
  console.log('Runtime config available:', isRuntimeConfigAvailable());
  
  if (typeof window !== 'undefined') {
    console.log('window.NEXT_PUBLIC_API_URL:', window.NEXT_PUBLIC_API_URL);
  }
  
  // Check build-time config
  console.log('Build-time API URL:', process.env.NEXT_PUBLIC_API_URL);
  
  // Get the resolved base URL
  const baseUrl = getApiBaseUrl();
  console.log('Resolved base URL:', baseUrl);
  
  // Test a sample URL
  const sampleUrl = `${baseUrl}/api/v1/auth/login`;
  console.log('Sample login URL:', sampleUrl);
  
  console.log('=== End Test ===');
  
  return {
    isBrowser: typeof window !== 'undefined',
    runtimeConfigAvailable: isRuntimeConfigAvailable(),
    runtimeUrl: typeof window !== 'undefined' ? window.NEXT_PUBLIC_API_URL : undefined,
    buildTimeUrl: process.env.NEXT_PUBLIC_API_URL,
    resolvedUrl: baseUrl,
    sampleUrl
  };
}

// Make it available globally for easy testing in browser console
if (typeof window !== 'undefined') {
  (window as any).testApiConfig = testApiConfig;
}