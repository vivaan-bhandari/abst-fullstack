#!/bin/bash

set -e  # Exit on any error

echo "Starting Django application..."
echo "Port: $PORT"
echo "Database URL: $DATABASE_URL"
echo "Debug: $DEBUG"
echo "Allowed Hosts: $ALLOWED_HOSTS"

# Start gunicorn immediately - no background, no complex checks
echo "Starting gunicorn..."
exec gunicorn abst.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --preload 