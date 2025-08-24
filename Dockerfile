# Use Python 3.9 slim image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=abst.settings

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y \
    nodejs \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend code
COPY frontend/ ./frontend/

# Copy deployment data if it exists
COPY deployment_data/ ./deployment_data/ 2>/dev/null || true

# Install frontend dependencies
WORKDIR /app/frontend
RUN npm install

# Build the React app
RUN npm run build

# Copy built React app to Django static files
WORKDIR /app
RUN mkdir -p staticfiles
RUN cp -r frontend/build/* staticfiles/

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Starting Django server..."\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
echo "Importing deployment data if available..."\n\
if [ -d "deployment_data" ] && [ -f "deployment_data/summary.json" ]; then\n\
    echo "Found deployment data, importing..."\n\
    python import_deployment_data.py\n\
else\n\
    echo "No deployment data found, skipping import"\n\
fi\n\
PORT=${PORT:-8000}\n\
echo "Starting server on port $PORT"\n\
gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 abst.wsgi:application' > start.sh

RUN chmod +x start.sh

# Expose port
EXPOSE 8000

# Start the application
CMD ["./start.sh"] 