// Runtime configuration - loaded by browser
(function() {
  // Initialize with a default that will be replaced by docker-entrypoint.sh
  if (!window.NEXT_PUBLIC_API_URL) {
    window.NEXT_PUBLIC_API_URL = '__PLACEHOLDER__';
  }
})();
