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

# Check if gunicorn is running by checking the port
echo "Checking if gunicorn is running on port $PORT..."
sleep 10  # Give gunicorn more time to start

# Try to connect to the port to see if server is responding
if command -v curl >/dev/null 2>&1; then
    if curl -s "http://localhost:$PORT/" >/dev/null 2>&1; then
        echo "✅ Gunicorn is running and responding on port $PORT"
    else
        echo "❌ Gunicorn is not responding on port $PORT"
        exit 1
    fi
else
    # Fallback: just check if port is listening
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln | grep ":$PORT " >/dev/null 2>&1; then
            echo "✅ Port $PORT is listening (gunicorn likely running)"
        else
            echo "❌ Port $PORT is not listening"
            exit 1
        fi
    else
        # Last resort: just assume it's working after delay
        echo "⚠️  Cannot verify gunicorn status, assuming it's running after delay"
    fi
fi

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
while true; do
    # Check if port is still listening
    if command -v netstat >/dev/null 2>&1; then
        if ! netstat -tuln | grep ":$PORT " >/dev/null 2>&1; then
            echo "❌ Port $PORT stopped listening - gunicorn may have crashed"
            exit 1
        fi
    fi
    
    # Check if server is responding
    if command -v curl >/dev/null 2>&1; then
        if ! curl -s "http://localhost:$PORT/" >/dev/null 2>&1; then
            echo "❌ Server stopped responding - gunicorn may have crashed"
            exit 1
        fi
    fi
    
    sleep 30
done 