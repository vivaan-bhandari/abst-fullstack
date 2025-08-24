#!/usr/bin/env python3
"""
Import deployment data on Railway
This script imports all exported data to restore the exact local state
"""

import os
import sys
import django
import json
from django.core.serializers import deserialize
from django.db import transaction

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

def import_data():
    """Import all data from JSON files"""
    
    export_dir = 'deployment_data'
    
    if not os.path.exists(export_dir):
        print(f"❌ Export directory {export_dir} not found!")
        print("Please run export_local_data.py first")
        return
    
    print("📥 Importing deployment data...")
    
    try:
        with transaction.atomic():
            # Import Users (skip if they exist)
            print("👥 Importing users...")
            if os.path.exists(f'{export_dir}/users.json'):
                with open(f'{export_dir}/users.json', 'r') as f:
                    users_data = f.read()
                    for obj in deserialize('json', users_data):
                        obj.save()
            
            # Import Facilities
            print("🏥 Importing facilities...")
            if os.path.exists(f'{export_dir}/facilities.json'):
                with open(f'{export_dir}/facilities.json', 'r') as f:
                    facilities_data = f.read()
                    for obj in deserialize('json', facilities_data):
                        obj.save()
            
            # Import Facility Access
            print("🔑 Importing facility access...")
            if os.path.exists(f'{export_dir}/facility_access.json'):
                with open(f'{export_dir}/facility_access.json', 'r') as f:
                    access_data = f.read()
                    for obj in deserialize('json', access_data):
                        obj.save()
            
            # Import Residents
            print("👴 Importing residents...")
            if os.path.exists(f'{export_dir}/residents.json'):
                with open(f'{export_dir}/residents.json', 'r') as f:
                    residents_data = f.read()
                    for obj in deserialize('json', residents_data):
                        obj.save()
            
            # Import ADL Questions
            print("❓ Importing ADL questions...")
            if os.path.exists(f'{export_dir}/adl_questions.json'):
                with open(f'{export_dir}/adl_questions.json', 'r') as f:
                    adl_questions_data = f.read()
                    for obj in deserialize('json', adl_questions_data):
                        obj.save()
            
            # Import ADLs
            print("📊 Importing ADLs...")
            if os.path.exists(f'{export_dir}/adls.json'):
                with open(f'{export_dir}/adls.json', 'r') as f:
                    adls_data = f.read()
                    for obj in deserialize('json', adls_data):
                        obj.save()
            
            # Import Shift Templates
            print("⏰ Importing shift templates...")
            if os.path.exists(f'{export_dir}/shift_templates.json'):
                with open(f'{export_dir}/shift_templates.json', 'r') as f:
                    shift_templates_data = f.read()
                    for obj in deserialize('json', shift_templates_data):
                        obj.save()
            
            # Import Staff Assignments
            print("👷 Importing staff assignments...")
            if os.path.exists(f'{export_dir}/staff_assignments.json'):
                with open(f'{export_dir}/staff_assignments.json', 'r') as f:
                    staff_assignments_data = f.read()
                    for obj in deserialize('json', staff_assignments_data):
                        obj.save()
            
            print("✅ All data imported successfully!")
            
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        raise

if __name__ == '__main__':
    import_data()
