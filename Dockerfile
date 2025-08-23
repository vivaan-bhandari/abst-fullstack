FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy the entire project first
COPY . .

# Install Python dependencies from backend requirements
RUN pip install --no-cache-dir -r backend/requirements.txt

# Change to backend directory
WORKDIR /app/backend

# Collect static files only (migrations will run at startup)
RUN python manage.py collectstatic --noinput

# Copy the startup script
COPY backend/start.sh /app/backend/start.sh
RUN chmod +x /app/backend/start.sh

# Expose port
EXPOSE $PORT

# Start command with better error handling
CMD ["/app/backend/start.sh"] 