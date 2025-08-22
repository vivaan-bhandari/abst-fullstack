#!/usr/bin/env python3
"""
Debug script to understand why Murray's AI recommendations are incomplete
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abst.settings')
django.setup()

from adls.models import ADL
from residents.models import Resident, FacilitySection
from scheduling.models import Staff, ShiftTemplate
from django.db.models import Q

def debug_murray_adl():
    """Debug Murray's ADL data to understand incomplete recommendations"""
    
    # Find Murray facility
    try:
        murray_section = FacilitySection.objects.filter(
            facility__name__icontains='Murray'
        ).first()
        
        if not murray_section:
            print("❌ Murray facility not found")
            return
            
        murray_facility = murray_section.facility
        print(f"🔍 Analyzing Murray facility: {murray_facility.name} (ID: {murray_facility.id})")
        print(f"   Section: {murray_section.name} (ID: {murray_section.id})")
        
        # Check residents
        residents = Resident.objects.filter(facility_section__facility=murray_facility)
        print(f"\n👥 Residents: {residents.count()}")
        
        # Check ADL data for last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        adls = ADL.objects.filter(
            resident__facility_section__facility=murray_facility,
            is_deleted=False,
            created_at__range=(start_date, end_date)
        )
        
        print(f"\n📊 ADL Records (last 30 days): {adls.count()}")
        
        if adls.count() == 0:
            print("❌ No ADL records found in the last 30 days!")
            return
            
        # Sample ADL record structure
        sample_adl = adls.first()
        print(f"\n🔍 Sample ADL Record Structure:")
        print(f"   ID: {sample_adl.id}")
        print(f"   Resident: {sample_adl.resident.name}")
        print(f"   Question: {sample_adl.question_text}")
        print(f"   Total Hours: {sample_adl.total_hours}")
        print(f"   Minutes: {getattr(sample_adl, 'minutes', 'N/A')}")
        print(f"   Frequency: {getattr(sample_adl, 'frequency', 'N/A')}")
        print(f"   Status: {sample_adl.status}")
        print(f"   Created: {sample_adl.created_at}")
        
        # Check per_day_shift_times field
        if hasattr(sample_adl, 'per_day_shift_times'):
            shift_times = sample_adl.per_day_shift_times
            print(f"   Per Day Shift Times: {shift_times}")
            
            if isinstance(shift_times, dict):
                print(f"   Shift Time Keys: {list(shift_times.keys())}")
                
                # Check for expected keys
                expected_keys = [
                    'MonShift1Time', 'MonShift2Time', 'MonShift3Time',
                    'TuesShift1Time', 'TuesShift2Time', 'TuesShift3Time',
                    'WedShift1Time', 'WedShift2Time', 'WedShift3Time',
                    'ThursShift1Time', 'ThursShift2Time', 'ThursShift3Time',
                    'FriShift1Time', 'FriShift2Time', 'FriShift3Time',
                    'SatShift1Time', 'SatShift2Time', 'SatShift3Time',
                    'SunShift1Time', 'SunShift2Time', 'SunShift3Time'
                ]
                
                missing_keys = [key for key in expected_keys if key not in shift_times]
                print(f"   Missing Keys: {missing_keys}")
                
                # Check values for each day
                days = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
                shifts = ['Shift1Time', 'Shift2Time', 'Shift3Time']
                
                print(f"\n📅 Daily Shift Time Values:")
                for day in days:
                    print(f"   {day}:")
                    for shift in shifts:
                        key = f"{day}{shift}"
                        value = shift_times.get(key, 'Missing')
                        print(f"     {shift}: {value}")
        else:
            print("   ❌ per_day_shift_times field not found!")
            
        # Check ADL data distribution by day
        print(f"\n📈 ADL Data Distribution by Day:")
        for i in range(7):
            check_date = start_date + timedelta(days=i)
            day_name = check_date.strftime('%a')
            day_adls = adls.filter(created_at__date=check_date.date())
            print(f"   {day_name}: {day_adls.count()} records")
            
        # Check shift templates
        shift_templates = ShiftTemplate.objects.filter(facility=murray_facility, is_active=True)
        print(f"\n⏰ Shift Templates: {shift_templates.count()}")
        for template in shift_templates:
            print(f"   - {template.name} ({template.shift_type})")
            
        # Check staff
        staff = Staff.objects.filter(facility=murray_facility, status='active')
        print(f"\n👨‍⚕️ Active Staff: {staff.count()}")
        
        # Summary of why recommendations might be incomplete
        print(f"\n🔍 Analysis Summary:")
        print(f"   The AI engine looks for ADL records with 'per_day_shift_times' field")
        print(f"   containing keys like 'MonShift1Time', 'TuesShift2Time', etc.")
        print(f"   If these fields are missing or have 0 values, those shifts won't get recommendations.")
        print(f"   This explains why Tuesday, Thursday, and most SWING shifts show 'No data'.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_murray_adl()
