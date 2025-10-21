#!/bin/sh
set -e

# Function to validate URL format
validate_url() {
  if ! echo "$1" | grep -E '^https?://[^ ]+$' > /dev/null; then
    echo "Error: Invalid URL format: $1"
    exit 1
  fi
}

# Replace placeholder with actual API URL at runtime
if [ -n "$NEXT_PUBLIC_API_URL" ]; then
  echo "Configuring API URL: $NEXT_PUBLIC_API_URL"
  
  # Validate URL format
  validate_url "$NEXT_PUBLIC_API_URL"
  
  # Update the config.js file with the actual API URL
  cat > /app/public/config.js <<EOF
// Runtime configuration - loaded by browser
(function() {
  window.NEXT_PUBLIC_API_URL = '$NEXT_PUBLIC_API_URL';
})();
EOF

  echo "API URL configuration completed successfully"
else
  echo "Warning: NEXT_PUBLIC_API_URL not set, using build-time configuration"
fi

# Execute the CMD
exec "$@"
