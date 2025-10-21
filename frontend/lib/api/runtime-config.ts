/**
 * Runtime configuration utilities to ensure API URL is properly loaded
 */

/**
 * Wait for runtime configuration to be available
 * This is useful for components that need to ensure the config is loaded before making API calls
 */
export function waitForRuntimeConfig(timeoutMs: number = 5000): Promise<void> {
  return new Promise((resolve, reject) => {
    // Check if config is already available
    if (typeof window !== 'undefined' && 
        window.NEXT_PUBLIC_API_URL && 
        window.NEXT_PUBLIC_API_URL !== '__PLACEHOLDER__') {
      resolve();
      return;
    }

    // If not in browser, resolve immediately (will use build-time config)
    if (typeof window === 'undefined') {
      resolve();
      return;
    }

    let attempts = 0;
    const maxAttempts = timeoutMs / 100; // Check every 100ms

    const interval = setInterval(() => {
      attempts++;
      
      // Check if config is now available
      if (window.NEXT_PUBLIC_API_URL && 
          window.NEXT_PUBLIC_API_URL !== '__PLACEHOLDER__') {
        clearInterval(interval);
        resolve();
        return;
      }

      // Timeout after max attempts
      if (attempts >= maxAttempts) {
        clearInterval(interval);
        console.warn('Runtime configuration not available after timeout, using fallback');
        resolve(); // Resolve anyway to allow fallback to build-time config
      }
    }, 100);
  });
}

/**
 * Check if runtime configuration is available and valid
 */
export function isRuntimeConfigAvailable(): boolean {
  return typeof window !== 'undefined' &&
         !!window.NEXT_PUBLIC_API_URL &&
         window.NEXT_PUBLIC_API_URL !== '__PLACEHOLDER__';
}