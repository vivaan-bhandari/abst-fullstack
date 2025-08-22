#!/usr/bin/env python
"""
Management script to calculate acuity staffing requirements for existing facilities
based on their ADL data. This can be run manually or scheduled.

Usage:
    python manage.py shell
    exec(open('calculate_acuity_staffing.py').read())
"""

import os
import django
from decimal import Decimal
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abst.settings')
django.setup()

from adls.models import ADL
from residents.models import Resident, Facility
from scheduling.models import AcuityBasedStaffing, Shift, ShiftTemplate

def calculate_acuity_staffing_for_facility(facility_id):
    """Calculate acuity staffing requirements for a specific facility"""
    try:
        facility = Facility.objects.get(id=facility_id)
        print(f"Calculating acuity staffing for facility: {facility.name}")
        
        # Get all shift templates for this facility
        shift_templates = ShiftTemplate.objects.filter(facility=facility)
        if not shift_templates.exists():
            print(f"No shift templates found for facility {facility.name}")
            return
        
        # Get all residents in this facility
        facility_residents = Resident.objects.filter(facility_section__facility=facility)
        if not facility_residents.exists():
            print(f"No residents found for facility {facility.name}")
            return
        
        print(f"Found {facility_residents.count()} residents and {shift_templates.count()} shift templates")
        
        for template in shift_templates:
            print(f"\nProcessing shift template: {template.name} ({template.shift_type} shift {template.shift_number})")
            
            # Calculate total care hours needed for this shift type
            total_care_hours = Decimal('0.0')
            high_acuity_count = 0
            medium_acuity_count = 0
            low_acuity_count = 0
            
            for resident in facility_residents:
                # Get ADL data for this resident
                resident_adls = ADL.objects.filter(
                    resident=resident,
                    is_deleted=False
                )
                
                # Calculate total care minutes for this shift type
                shift_care_minutes = 0
                for adl in resident_adls:
                    # Get the specific shift time for this template's shift type
                    shift_key = f"ResidentTotal{template.shift_type.capitalize()}Shift{template.shift_number}Time"
                    if shift_key in adl.per_day_shift_times:
                        shift_care_minutes += adl.per_day_shift_times.get(shift_key, 0)
                
                # Convert to hours
                shift_care_hours = Decimal(str(shift_care_minutes)) / Decimal('60.0')
                total_care_hours += shift_care_hours
                
                # Categorize by acuity level (based on care hours needed)
                if shift_care_hours >= Decimal('2.0'):  # 2+ hours = high acuity
                    high_acuity_count += 1
                elif shift_care_hours >= Decimal('1.0'):  # 1-2 hours = medium acuity
                    medium_acuity_count += 1
                else:  # <1 hour = low acuity
                    low_acuity_count += 1
            
            # Calculate recommended staff count based on care hours
            # Industry standard: 1 staff per 8 hours of care needed
            recommended_staff = max(1, int(total_care_hours / Decimal('8.0')))
            
            # Calculate skill mix (basic breakdown)
            skill_mix = {
                'CNA': max(1, int(recommended_staff * 0.7)),  # 70% CNAs
                'LPN': max(1, int(recommended_staff * 0.2)),  # 20% LPNs
                'RN': max(1, int(recommended_staff * 0.1)),   # 10% RNs
            }
            
            print(f"  Total care hours needed: {total_care_hours}")
            print(f"  High acuity residents: {high_acuity_count}")
            print(f"  Medium acuity residents: {medium_acuity_count}")
            print(f"  Low acuity residents: {low_acuity_count}")
            print(f"  Recommended staff: {recommended_staff}")
            print(f"  Skill mix: {skill_mix}")
            
            # Create or update acuity staffing requirement
            try:
                # Try to find an existing shift for this template, or create a placeholder
                shift, _ = Shift.objects.get_or_create(
                    shift_template=template,
                    facility=facility,
                    date=datetime.now().date(),  # Use today's date as placeholder
                    defaults={
                        'start_time': template.start_time,
                        'end_time': template.end_time,
                        'facility': facility
                    }
                )
                
                # Create or update acuity staffing requirement
                acuity_staffing, created = AcuityBasedStaffing.objects.update_or_create(
                    shift=shift,
                    defaults={
                        'total_care_hours_needed': total_care_hours,
                        'high_acuity_residents': high_acuity_count,
                        'medium_acuity_residents': medium_acuity_count,
                        'low_acuity_residents': low_acuity_count,
                        'recommended_staff_count': recommended_staff,
                        'recommended_skill_mix': skill_mix,
                    }
                )
                
                if created:
                    print(f"  ✓ Created new acuity staffing requirement")
                else:
                    print(f"  ✓ Updated existing acuity staffing requirement")
                    
            except Exception as e:
                print(f"  ✗ Error creating acuity staffing: {str(e)}")
                continue
        
        print(f"\n✓ Completed acuity staffing calculation for {facility.name}")
        
    except Facility.DoesNotExist:
        print(f"Facility with ID {facility_id} not found")
    except Exception as e:
        print(f"Error calculating acuity staffing for facility {facility_id}: {str(e)}")

def calculate_acuity_staffing_for_all_facilities():
    """Calculate acuity staffing requirements for all facilities"""
    facilities = Facility.objects.all()
    print(f"Found {facilities.count()} facilities")
    
    for facility in facilities:
        print(f"\n{'='*50}")
        calculate_acuity_staffing_for_facility(facility.id)
    
    print(f"\n{'='*50}")
    print("Completed acuity staffing calculation for all facilities")

if __name__ == "__main__":
    # Example usage:
    # Calculate for a specific facility
    # calculate_acuity_staffing_for_facility(1)
    
    # Calculate for all facilities
    calculate_acuity_staffing_for_all_facilities()
