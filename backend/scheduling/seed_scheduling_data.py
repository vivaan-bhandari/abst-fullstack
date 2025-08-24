#!/usr/bin/env python
"""
Seed script to populate the scheduling system with sample data
"""
import os
import sys
import django
from datetime import datetime, timedelta, time
from decimal import Decimal

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abst.settings')
django.setup()

from scheduling.models import (
    Staff, ShiftTemplate, Shift, StaffAssignment, 
    StaffAvailability, AIInsight, AIRecommendation
)
from residents.models import Facility
from django.contrib.auth.models import User


def create_sample_data():
    """Create sample data for the scheduling system"""
    
    # Get or create a facility
    facility, created = Facility.objects.get_or_create(
        name="Markham House Assisted Living",
        defaults={
            'address': '123 Main St, Markham, CA',
            'phone': '(555) 123-4567',
            'email': 'info@markhamhouse.com'
        }
    )
    
    if created:
        print(f"Created facility: {facility.name}")
    else:
        print(f"Using existing facility: {facility.name}")
    
    # Create shift templates
    shift_templates = [
        {
            'template_name': 'Day Shift',
            'shift_type': 'day',
            'start_time': time(6, 0),  # 6:00 AM
            'end_time': time(14, 0),   # 2:00 PM
            'duration': Decimal('8.00'),
            'required_staff': 3,
            'is_active': True,
            'facility': facility
        },
        {
            'template_name': 'Swing Shift',
            'shift_type': 'swing',
            'start_time': time(14, 0), # 2:00 PM
            'end_time': time(22, 0),   # 10:00 PM
            'duration': Decimal('8.00'),
            'required_staff': 2,
            'is_active': True,
            'facility': facility
        },
        {
            'template_name': 'NOC Shift',
            'shift_type': 'noc',
            'start_time': time(22, 0), # 10:00 PM
            'end_time': time(6, 0),    # 6:00 AM
            'duration': Decimal('8.00'),
            'required_staff': 2,
            'is_active': True,
            'facility': facility
        }
    ]
    
    created_templates = []
    for template_data in shift_templates:
        template, created = ShiftTemplate.objects.get_or_create(
            template_name=template_data['template_name'],
            facility=facility,
            defaults=template_data
        )
        created_templates.append(template)
        if created:
            print(f"Created shift template: {template.template_name}")
        else:
            print(f"Using existing shift template: {template.template_name}")
    
    # Create sample staff
    staff_members = [
        {
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'email': 'sarah.johnson@markhamhouse.com',
            'employee_id': 'EMP001',
            'role': 'cna',
            'hire_date': datetime.now().date() - timedelta(days=365),
            'status': 'active',
            'max_hours': 40,
            'notes': 'Experienced CNA with 5 years in senior care',
            'facility': facility
        },
        {
            'first_name': 'Michael',
            'last_name': 'Chen',
            'email': 'michael.chen@markhamhouse.com',
            'employee_id': 'EMP002',
            'role': 'lpn',
            'hire_date': datetime.now().date() - timedelta(days=180),
            'status': 'active',
            'max_hours': 40,
            'notes': 'LPN with medication administration certification',
            'facility': facility
        },
        {
            'first_name': 'Emily',
            'last_name': 'Rodriguez',
            'email': 'emily.rodriguez@markhamhouse.com',
            'employee_id': 'EMP003',
            'role': 'cna',
            'hire_date': datetime.now().date() - timedelta(days=90),
            'status': 'active',
            'max_hours': 32,
            'notes': 'Part-time CNA, available for day and swing shifts',
            'facility': facility
        },
        {
            'first_name': 'David',
            'last_name': 'Thompson',
            'email': 'david.thompson@markhamhouse.com',
            'employee_id': 'EMP004',
            'role': 'cna',
            'hire_date': datetime.now().date() - timedelta(days=120),
            'status': 'active',
            'max_hours': 40,
            'notes': 'CNA with dementia care specialization',
            'facility': facility
        }
    ]
    
    created_staff = []
    for staff_data in staff_members:
        staff, created = Staff.objects.get_or_create(
            email=staff_data['email'],
            defaults=staff_data
        )
        created_staff.append(staff)
        if created:
            print(f"Created staff member: {staff.full_name}")
        else:
            print(f"Using existing staff member: {staff.full_name}")
    
    # Create shifts for the current week
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    created_shifts = []
    for i in range(7):  # 7 days
        shift_date = week_start + timedelta(days=i)
        
        for template in created_templates:
            shift, created = Shift.objects.get_or_create(
                date=shift_date,
                shift_template=template,
                facility=facility,
                defaults={
                    'required_staff_count': template.required_staff,
                    'required_staff_role': 'cna'
                }
            )
            created_shifts.append(shift)
            if created:
                print(f"Created shift: {shift.shift_template.template_name} on {shift_date}")
            else:
                print(f"Using existing shift: {shift.shift_template.template_name} on {shift_date}")
    
    # Create some staff assignments
    for i, shift in enumerate(created_shifts[:10]):  # Assign first 10 shifts
        staff_member = created_staff[i % len(created_staff)]
        assignment, created = StaffAssignment.objects.get_or_create(
            staff=staff_member,
            shift=shift,
            defaults={
                'status': 'assigned'
            }
        )
        if created:
            print(f"Created assignment: {staff_member.full_name} to {shift}")
        else:
            print(f"Using existing assignment: {staff_member.full_name} to {shift}")
    
    # Create staff availability for the week
    for staff_member in created_staff:
        for i in range(7):
            availability_date = week_start + timedelta(days=i)
            availability, created = StaffAvailability.objects.get_or_create(
                staff=staff_member,
                date=availability_date,
                facility=facility,
                defaults={
                    'availability_status': 'available',
                    'max_hours': 8,
                    'preferred_shift_types': ['day', 'swing'] if staff_member.role == 'cna' else ['day']
                }
            )
            if created:
                print(f"Created availability: {staff_member.full_name} for {availability_date}")
            else:
                print(f"Using existing availability: {staff_member.full_name} for {availability_date}")
    
    # Create AI insights
    ai_insight, created = AIInsight.objects.get_or_create(
        facility=facility,
        date=today,
        defaults={
            'total_residents': 45,
            'total_care_hours': Decimal('180.50'),
            'avg_acuity_score': Decimal('3.2'),
            'staffing_efficiency': 87,
            'low_acuity_count': 15,
            'medium_acuity_count': 20,
            'high_acuity_count': 10
        }
    )
    if created:
        print(f"Created AI insight for {today}")
    else:
        print(f"Using existing AI insight for {today}")
    
    # Create AI recommendations for the week
    for i in range(7):
        rec_date = week_start + timedelta(days=i)
        for template in created_templates:
            recommendation, created = AIRecommendation.objects.get_or_create(
                facility=facility,
                date=rec_date,
                shift_type=template.shift_type,
                defaults={
                    'care_hours': Decimal('8.00'),
                    'required_staff': template.required_staff,
                    'resident_count': 45,
                    'confidence': 85 + (i * 2),  # Varying confidence
                    'applied': False
                }
            )
            if created:
                print(f"Created AI recommendation: {template.shift_type} shift for {rec_date}")
            else:
                print(f"Using existing AI recommendation: {template.shift_type} shift for {rec_date}")
    
    print("\n✅ Sample scheduling data created successfully!")
    print(f"📊 Created {len(created_staff)} staff members")
    print(f"⏰ Created {len(created_templates)} shift templates")
    print(f"📅 Created {len(created_shifts)} shifts")
    print(f"🏥 Facility: {facility.name}")


if __name__ == '__main__':
    create_sample_data()
