#!/bin/sh
set -e

# Replace placeholder with actual API URL at runtime
if [ -n "$NEXT_PUBLIC_API_URL" ]; then
  echo "Configuring API URL: $NEXT_PUBLIC_API_URL"
  
  # Update the config.js file with the actual API URL
  cat > /app/public/config.js <<EOF
window.NEXT_PUBLIC_API_URL = '$NEXT_PUBLIC_API_URL';
EOF
fi

# Execute the CMD
exec "$@"
