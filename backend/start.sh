#!/bin/bash
# Start script for Railway deployment

set -e

echo "Starting Django application..."
echo "Port: $PORT"
echo "Database URL: $DATABASE_URL"

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Add Brighton facilities
echo "Setting up facilities..."
python add_brighton_facilities.py

# Seed ADL questions
echo "Seeding ADL questions..."
python adls/seed_adl_questions.py

# Create superuser if it doesn't exist
echo "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='superadmin').exists():
    User.objects.create_superuser('superadmin', 'superadmin@example.com', 'superpass123')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Grant facility access to all users
echo "Granting facility access to users..."
python manage.py shell -c "
from django.contrib.auth.models import User
from users.models import FacilityAccess
from residents.models import Facility

users = User.objects.all()
facilities = Facility.objects.all()

for user in users:
    for facility in facilities:
        access, created = FacilityAccess.objects.get_or_create(
            user=user,
            facility=facility,
            defaults={
                'role': 'admin' if user.is_staff else 'staff',
                'status': 'approved'
            }
        )
        if not created and access.status != 'approved':
            access.status = 'approved'
            access.role = 'admin' if user.is_staff else 'staff'
            access.save()

print(f'Granted facility access to {users.count()} users for {facilities.count()} facilities')
"

# Start gunicorn
echo "Starting gunicorn..."
exec gunicorn abst.wsgi --bind 0.0.0.0:$PORT --log-file - --workers 2 