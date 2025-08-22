#!/usr/bin/env python3
"""
Debug script to trace through the AI engine's data loading process step by step
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

from scheduling.ai_recommendations import AIShiftRecommendationEngine
from residents.models import FacilitySection
from adls.models import ADL
from residents.models import Resident
import pandas as pd
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.DEBUG)

def debug_ai_data_loading():
    """Debug the AI engine's data loading process step by step"""
    
    try:
        # Find Murray facility
        murray_section = FacilitySection.objects.filter(
            facility__name__icontains='Murray'
        ).first()
        
        if not murray_section:
            print("❌ Murray facility not found")
            return
            
        murray_facility = murray_section.facility
        print(f"🔍 Debugging AI data loading for Murray facility: {murray_facility.name}")
        
        # Create AI engine instance
        ai_engine = AIShiftRecommendationEngine(murray_facility.id)
        
        # Step 1: Check if load_data method exists
        print(f"\n📋 Step 1: Checking AI engine methods...")
        print(f"   Available methods: {[method for method in dir(ai_engine) if not method.startswith('_')]}")
        
        # Step 2: Check if load_data method exists and call it
        if hasattr(ai_engine, 'load_data'):
            print(f"\n📋 Step 2: Calling load_data method...")
            try:
                ai_engine.load_data()
                print(f"   ✅ load_data() called successfully")
                
                # Check what data was loaded
                if hasattr(ai_engine, 'adl_data') and ai_engine.adl_data is not None:
                    print(f"   📊 ADL data loaded: {len(ai_engine.adl_data)} records")
                    if len(ai_engine.adl_data) > 0:
                        print(f"   📋 Sample ADL record columns: {list(ai_engine.adl_data.columns)}")
                        print(f"   📋 Sample ADL record:")
                        print(ai_engine.adl_data.iloc[0].to_dict())
                else:
                    print(f"   ❌ No ADL data loaded")
                    
                if hasattr(ai_engine, 'resident_data') and ai_engine.resident_data is not None:
                    print(f"   👥 Resident data loaded: {len(ai_engine.resident_data)} records")
                else:
                    print(f"   ❌ No resident data loaded")
                    
                if hasattr(ai_engine, 'staff_data') and ai_engine.staff_data is not None:
                    print(f"   👨‍⚕️ Staff data loaded: {len(ai_engine.staff_data)} records")
                else:
                    print(f"   ❌ No staff data loaded")
                    
            except Exception as e:
                print(f"   ❌ Error calling load_data: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ❌ load_data method not found!")
            
        # Step 3: Check if we can manually load the data
        print(f"\n📋 Step 3: Manually checking data availability...")
        
        # Check ADL data directly
        adls = ADL.objects.filter(
            resident__facility_section__facility=murray_facility,
            is_deleted=False
        )
        print(f"   📊 Total ADL records in database: {adls.count()}")
        
        if adls.count() > 0:
            # Check recent ADLs
            recent_adls = adls.filter(created_at__gte=datetime.now() - timedelta(days=30))
            print(f"   📊 Recent ADL records (last 30 days): {recent_adls.count()}")
            
            # Check ADLs with non-zero total_hours
            non_zero_adls = adls.filter(total_hours__gt=0)
            print(f"   📊 ADLs with non-zero total_hours: {non_zero_adls.count()}")
            
            # Sample ADL record
            sample_adl = adls.first()
            print(f"   📋 Sample ADL record:")
            print(f"      ID: {sample_adl.id}")
            print(f"      Resident: {sample_adl.resident.name}")
            print(f"      Total Hours: {sample_adl.total_hours}")
            print(f"      Minutes: {getattr(sample_adl, 'minutes', 'N/A')}")
            print(f"      Frequency: {getattr(sample_adl, 'frequency', 'N/A')}")
            print(f"      Status: {sample_adl.status}")
            
            # Check per_day_shift_times
            if hasattr(sample_adl, 'per_day_shift_times'):
                shift_times = sample_adl.per_day_shift_times
                if isinstance(shift_times, dict):
                    non_zero_count = sum(1 for v in shift_times.values() if v and v > 0)
                    print(f"      Per Day Shift Times: {non_zero_count} non-zero values out of {len(shift_times)}")
                else:
                    print(f"      Per Day Shift Times: {shift_times} (not a dict)")
            else:
                print(f"      Per Day Shift Times: field not found")
        
        # Check residents
        residents = Resident.objects.filter(facility_section__facility=murray_facility)
        print(f"   👥 Total residents: {residents.count()}")
        
        # Step 4: Try to manually create the data structure the AI engine expects
        print(f"\n📋 Step 4: Manually creating data structure...")
        
        if adls.count() > 0:
            # Convert ADLs to DataFrame
            adl_list = []
            for adl in adls[:100]:  # Limit to first 100 for testing
                adl_dict = {
                    'id': adl.id,
                    'resident_id': adl.resident.id,
                    'total_hours': adl.total_hours or 0,
                    'minutes': getattr(adl, 'minutes', 0) or 0,
                    'frequency': getattr(adl, 'frequency', 0) or 0,
                    'status': adl.status,
                    'per_day_shift_times': getattr(adl, 'per_day_shift_times', {}) or {}
                }
                adl_list.append(adl_dict)
            
            adl_df = pd.DataFrame(adl_list)
            print(f"   📊 Created ADL DataFrame: {len(adl_df)} records")
            print(f"   📋 DataFrame columns: {list(adl_df.columns)}")
            
            if len(adl_df) > 0:
                print(f"   📋 Sample DataFrame row:")
                print(adl_df.iloc[0].to_dict())
                
                # Check if we have any non-zero total_hours
                non_zero_hours = adl_df[adl_df['total_hours'] > 0]
                print(f"   📊 Rows with non-zero total_hours: {len(non_zero_hours)}")
                
                if len(non_zero_hours) > 0:
                    print(f"   📊 Total care hours in DataFrame: {non_zero_hours['total_hours'].sum():.2f}")
        
    except Exception as e:
        print(f"❌ Error debugging AI data loading: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ai_data_loading()
