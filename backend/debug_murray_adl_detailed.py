#!/usr/bin/env python3
"""
Detailed debug script to understand Murray's ADL data structure and why care hours exist for all days
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
from django.db.models import Q, Sum
import json

def debug_murray_adl_detailed():
    """Detailed debug of Murray's ADL data structure"""
    
    try:
        # Find Murray facility
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
            
        # Check total care hours across all ADLs
        total_care_hours = adls.aggregate(total=Sum('total_hours'))['total'] or 0
        print(f"\n📈 Total Care Hours (all ADLs): {total_care_hours:.2f}")
        
        # Check ADL records with non-zero total_hours
        non_zero_adls = adls.filter(total_hours__gt=0)
        print(f"📊 ADLs with non-zero total_hours: {non_zero_adls.count()}")
        
        # Sample multiple ADL records to see different patterns
        print(f"\n🔍 Sample ADL Records (showing different patterns):")
        
        for i, adl in enumerate(adls[:5]):  # Show first 5 ADLs
            print(f"\n   ADL #{i+1} (ID: {adl.id}):")
            print(f"     Resident: {adl.resident.name}")
            print(f"     Question: {adl.question_text[:60]}...")
            print(f"     Total Hours: {adl.total_hours}")
            print(f"     Minutes: {getattr(adl, 'minutes', 'N/A')}")
            print(f"     Frequency: {getattr(adl, 'frequency', 'N/A')}")
            print(f"     Status: {adl.status}")
            
            # Check per_day_shift_times field
            if hasattr(adl, 'per_day_shift_times'):
                shift_times = adl.per_day_shift_times
                if isinstance(shift_times, dict):
                    # Count non-zero values
                    non_zero_count = sum(1 for v in shift_times.values() if v and v > 0)
                    print(f"     Per Day Shift Times: {non_zero_count} non-zero values out of {len(shift_times)}")
                    
                    # Show non-zero values only
                    non_zero_values = {k: v for k, v in shift_times.items() if v and v > 0}
                    if non_zero_values:
                        print(f"     Non-zero values: {non_zero_values}")
                    else:
                        print(f"     All values are 0 or None")
            else:
                print(f"     ❌ per_day_shift_times field not found!")
        
        # Check if there are ADLs with different structures
        print(f"\n🔍 Checking for ADLs with different data structures:")
        
        # Look for ADLs that might have care hours calculated differently
        adls_with_minutes = adls.filter(minutes__gt=0)
        print(f"   ADLs with minutes > 0: {adls_with_minutes.count()}")
        
        adls_with_frequency = adls.filter(frequency__gt=0)
        print(f"   ADLs with frequency > 0: {adls_with_frequency.count()}")
        
        # Check if there are ADLs that calculate hours differently
        print(f"\n🔍 Understanding how care hours are calculated:")
        
        # Sample ADL with non-zero values
        sample_adl = adls.filter(total_hours__gt=0).first()
        if sample_adl:
            print(f"   Sample ADL with care hours:")
            print(f"     Total Hours: {sample_adl.total_hours}")
            print(f"     Minutes: {getattr(sample_adl, 'minutes', 'N/A')}")
            print(f"     Frequency: {getattr(sample_adl, 'frequency', 'N/A')}")
            
            # Calculate what the hours should be based on minutes and frequency
            minutes = getattr(sample_adl, 'minutes', 0) or 0
            frequency = getattr(sample_adl, 'frequency', 0) or 0
            
            if minutes > 0 and frequency > 0:
                calculated_hours = (minutes * frequency) / 60
                print(f"     Calculated Hours (minutes * frequency / 60): {calculated_hours:.2f}")
                print(f"     Difference from total_hours: {abs(calculated_hours - sample_adl.total_hours):.2f}")
        
        # Check if there are ADLs with different question types that might have different structures
        print(f"\n🔍 ADL Question Types:")
        question_types = adls.values_list('question_text', flat=True).distinct()
        print(f"   Total unique questions: {len(question_types)}")
        
        # Show first few question types
        for i, question in enumerate(question_types[:5]):
            print(f"     {i+1}. {question[:80]}...")
        
        # Summary
        print(f"\n🔍 Analysis Summary:")
        print(f"   The Murray Highland facility page shows care hours for ALL days (50-60 hours/day)")
        print(f"   But the AI engine's sample ADL record shows mostly 0 values in per_day_shift_times")
        print(f"   This suggests:")
        print(f"     1. ADL records DO have care hours (in total_hours field)")
        print(f"     2. The per_day_shift_times field might not be the primary source of care data")
        print(f"     3. The AI engine should use total_hours instead of relying on per_day_shift_times")
        print(f"     4. The facility page is correctly aggregating total_hours across all ADLs")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_murray_adl_detailed()
