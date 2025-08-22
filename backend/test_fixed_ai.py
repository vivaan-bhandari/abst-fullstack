#!/usr/bin/env python3
"""
Test script to verify the fixed AI engine generates recommendations for all days
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
import logging

# Set up logging to see debug output
logging.basicConfig(level=logging.INFO)

def test_fixed_ai_engine():
    """Test the fixed AI engine to see if it now generates recommendations for all days"""
    
    try:
        # Find Murray facility
        murray_section = FacilitySection.objects.filter(
            facility__name__icontains='Murray'
        ).first()
        
        if not murray_section:
            print("❌ Murray facility not found")
            return
            
        murray_facility = murray_section.facility
        print(f"🔍 Testing fixed AI engine for Murray facility: {murray_facility.name}")
        
        # Create AI engine instance
        ai_engine = AIShiftRecommendationEngine(murray_facility.id)
        
        # Test weekly recommendations
        print(f"\n📊 Testing weekly recommendations generation...")
        
        # Get the current week dates
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
        
        print(f"   Week dates: {[date.strftime('%a %m/%d') for date in week_dates]}")
        
        # Load data first
        print(f"   📋 Loading data...")
        ai_engine.load_data()
        
        # Generate recommendations
        weekly_recommendations = ai_engine.recommend_shifts_for_week(today)
        
        print(f"\n✅ Weekly recommendations generated: {len(weekly_recommendations)}")
        
        # Display the recommendations
        for rec in weekly_recommendations:
            print(f"   {rec['day']} {rec['shift_type'].upper()}: {rec['care_hours']:.2f}h care, {rec['staff_required']} staff, {rec['resident_count']} residents, {rec['confidence_score']}% confidence")
        
        # Check if we have recommendations for all days
        days_with_recommendations = set(rec['day'] for rec in weekly_recommendations)
        all_days = {'Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun'}
        missing_days = all_days - days_with_recommendations
        
        if missing_days:
            print(f"\n⚠️  Still missing recommendations for: {missing_days}")
        else:
            print(f"\n🎉 SUCCESS! All days now have recommendations!")
            
        # Check if we have recommendations for all shift types
        shift_types_with_recommendations = set(rec['shift_type'] for rec in weekly_recommendations)
        all_shift_types = {'day', 'swing', 'noc'}
        missing_shifts = all_shift_types - shift_types_with_recommendations
        
        if missing_shifts:
            print(f"⚠️  Still missing recommendations for shift types: {missing_shifts}")
        else:
            print(f"🎉 All shift types now have recommendations!")
            
    except Exception as e:
        print(f"❌ Error testing fixed AI engine: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_ai_engine()
