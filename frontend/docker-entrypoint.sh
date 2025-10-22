#!/bin/sh
set -e

# Simple entrypoint script - no longer needs to generate config.js
# The API configuration is now handled by NEXT_PUBLIC_ENV environment variable

# Execute the CMD
exec "$@"
