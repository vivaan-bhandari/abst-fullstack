#!/bin/bash

set -e  # Exit on any error

echo "Starting Django application..."
echo "Port: $PORT"
echo "Database URL: $DATABASE_URL"
echo "Debug: $DEBUG"
echo "Allowed Hosts: $ALLOWED_HOSTS"

# Start gunicorn immediately in the background
echo "Starting gunicorn immediately..."
gunicorn abst.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --preload \
    --daemon

# Wait a moment for gunicorn to start
sleep 5

# Check if gunicorn is running
if ! pgrep -f "gunicorn.*abst.wsgi:application" > /dev/null; then
    echo "ERROR: Gunicorn failed to start"
    exit 1
fi

echo "Gunicorn started successfully. PID: $(pgrep -f 'gunicorn.*abst.wsgi:application')"

# Now run setup tasks in the background
echo "Running setup tasks in background..."
{
    echo "Waiting for database to be ready..."
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Database connection attempt $attempt/$max_attempts..."
        
        # Try to connect to database using Django
        if python manage.py check --database default 2>/dev/null; then
            echo "Database is ready!"
            break
        fi
        
        echo "Database not ready, waiting 10 seconds..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "WARNING: Could not connect to database after $max_attempts attempts"
    else
        # Run migrations
        echo "Running migrations..."
        python manage.py migrate --noinput
        
        # Collect static files
        echo "Collecting static files..."
        python manage.py collectstatic --noinput
        
        echo "Setup tasks completed"
    fi
} &

# Keep the script running and monitor gunicorn
echo "Monitoring gunicorn process..."
while pgrep -f "gunicorn.*abst.wsgi:application" > /dev/null; do
    sleep 10
done

echo "Gunicorn process stopped unexpectedly"
exit 1 