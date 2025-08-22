#!/usr/bin/env python3
"""
Test script that directly tests AI engine methods step by step
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
import pandas as pd
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_ai_methods_step_by_step():
    """Test AI engine methods step by step"""
    
    try:
        # Find Murray facility
        murray_section = FacilitySection.objects.filter(
            facility__name__icontains='Murray'
        ).first()
        
        if not murray_section:
            print("❌ Murray facility not found")
            return
            
        murray_facility = murray_section.facility
        print(f"🔍 Testing AI methods step by step for Murray facility: {murray_facility.name}")
        
        # Create AI engine instance
        ai_engine = AIShiftRecommendationEngine(murray_facility.id)
        
        # Step 1: Load data
        print(f"\n📋 Step 1: Loading data...")
        ai_engine.load_data()
        print(f"   ✅ Data loaded: {len(ai_engine.adl_data)} ADL records")
        
        # Step 2: Check data structure
        print(f"\n📋 Step 2: Checking data structure...")
        if ai_engine.adl_data:
            sample_adl = ai_engine.adl_data[0]
            print(f"   📋 Sample ADL record:")
            for key, value in sample_adl.items():
                print(f"      {key}: {value} (type: {type(value)})")
        
        # Step 3: Test analyze_adl_patterns
        print(f"\n📋 Step 3: Testing analyze_adl_patterns...")
        try:
            adl_analysis = ai_engine.analyze_adl_patterns()
            print(f"   ✅ analyze_adl_patterns completed: {len(adl_analysis)} residents analyzed")
            
            if adl_analysis:
                # Show first resident analysis
                first_resident = list(adl_analysis.values())[0]
                print(f"   📋 First resident analysis:")
                for key, value in first_resident.items():
                    if key == 'daily_care_patterns':
                        print(f"      {key}: {value}")
                    else:
                        print(f"      {key}: {value}")
                        
        except Exception as e:
            print(f"   ❌ Error in analyze_adl_patterns: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 4: Test _analyze_daily_care_patterns directly
        print(f"\n📋 Step 4: Testing _analyze_daily_care_patterns directly...")
        try:
            if ai_engine.adl_data:
                # Convert to DataFrame
                df = pd.DataFrame(ai_engine.adl_data)
                print(f"   📊 DataFrame created: {len(df)} rows, {len(df.columns)} columns")
                
                # Get first resident's ADLs
                if 'resident_id' in df.columns:
                    first_resident_id = df['resident_id'].iloc[0]
                    resident_adls = df[df['resident_id'] == first_resident_id]
                    print(f"   👥 First resident ADLs: {len(resident_adls)} records")
                    
                    if len(resident_adls) > 0:
                        # Test the method directly
                        daily_patterns = ai_engine._analyze_daily_care_patterns(resident_adls)
                        print(f"   ✅ _analyze_daily_care_patterns completed")
                        print(f"   📊 Daily patterns: {daily_patterns}")
                        
                        # Check if we have any non-zero values
                        total_hours = sum(sum(shifts.values()) for shifts in daily_patterns.values())
                        print(f"   📈 Total care hours distributed: {total_hours:.2f}")
                        
        except Exception as e:
            print(f"   ❌ Error in _analyze_daily_care_patterns: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error testing AI methods: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ai_methods_step_by_step()
