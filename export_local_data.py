#!/usr/bin/env python3
"""
Export local data for deployment
This script exports all local data to JSON files that can be imported on Railway
"""

import os
import sys
import django
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abst.settings')
django.setup()

from django.contrib.auth.models import User
from residents.models import Resident
from adls.models import ADL, ADLQuestion
from users.models import Facility, FacilityAccess
from scheduling.models import ShiftTemplate, StaffAssignment
from django.core.serializers import serialize

def export_data():
    """Export all data to JSON files"""
    
    # Create export directory
    export_dir = 'deployment_data'
    os.makedirs(export_dir, exist_ok=True)
    
    print("📦 Exporting local data for deployment...")
    
    # Export Users
    print("👥 Exporting users...")
    users_data = serialize('json', User.objects.all())
    with open(f'{export_dir}/users.json', 'w') as f:
        f.write(users_data)
    
    # Export Facilities
    print("🏥 Exporting facilities...")
    facilities_data = serialize('json', Facility.objects.all())
    with open(f'{export_dir}/facilities.json', 'w') as f:
        f.write(facilities_data)
    
    # Export Facility Access
    print("🔑 Exporting facility access...")
    access_data = serialize('json', FacilityAccess.objects.all())
    with open(f'{export_dir}/facility_access.json', 'w') as f:
        f.write(access_data)
    
    # Export Residents
    print("👴 Exporting residents...")
    residents_data = serialize('json', Resident.objects.all())
    with open(f'{export_dir}/residents.json', 'w') as f:
        f.write(residents_data)
    
    # Export ADL Questions
    print("❓ Exporting ADL questions...")
    adl_questions_data = serialize('json', ADLQuestion.objects.all())
    with open(f'{export_dir}/adl_questions.json', 'w') as f:
        f.write(adl_questions_data)
    
    # Export ADLs
    print("📊 Exporting ADLs...")
    adls_data = serialize('json', ADL.objects.all())
    with open(f'{export_dir}/adls.json', 'w') as f:
        f.write(adls_data)
    
    # Export Shift Templates
    print("⏰ Exporting shift templates...")
    shift_templates_data = serialize('json', ShiftTemplate.objects.all())
    with open(f'{export_dir}/shift_templates.json', 'w') as f:
        f.write(shift_templates_data)
    
    # Export Staff Assignments
    print("👷 Exporting staff assignments...")
    staff_assignments_data = serialize('json', StaffAssignment.objects.all())
    with open(f'{export_dir}/staff_assignments.json', 'w') as f:
        f.write(staff_assignments_data)
    
    # Create a summary file
    summary = {
        'export_date': datetime.now().isoformat(),
        'total_users': User.objects.count(),
        'total_facilities': Facility.objects.count(),
        'total_residents': Resident.objects.count(),
        'total_adl_questions': ADLQuestion.objects.count(),
        'total_adls': ADL.objects.count(),
        'total_shift_templates': ShiftTemplate.objects.count(),
        'total_staff_assignments': StaffAssignment.objects.count(),
    }
    
    with open(f'{export_dir}/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Data exported to {export_dir}/")
    print(f"📊 Summary: {summary}")
    
    return export_dir

if __name__ == '__main__':
    export_data()
