#!/bin/bash

set -e  # Exit on any error

echo "Starting Django application..."
echo "Port: $PORT"
echo "Database URL: $DATABASE_URL"
echo "Debug: $DEBUG"
echo "Allowed Hosts: $ALLOWED_HOSTS"

# Function to check if database is ready
wait_for_db() {
    echo "Waiting for database to be ready..."
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Database connection attempt $attempt/$max_attempts..."
        
        # Try to connect to database using Django
        if python manage.py check --database default 2>/dev/null; then
            echo "Database is ready!"
            return 0
        fi
        
        echo "Database not ready, waiting 10 seconds..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo "Database connection failed after $max_attempts attempts"
    return 1
}

# Wait for database
if ! wait_for_db; then
    echo "ERROR: Could not connect to database. Exiting."
    exit 1
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn abst.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --preload \
    --max-requests 1000 \
    --max-requests-jitter 100 