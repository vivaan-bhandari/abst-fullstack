#!/usr/bin/env python
"""
Test script for the AI Recommendation Engine
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abst.settings')
django.setup()

from scheduling.ai_recommendations import AIShiftRecommendationEngine

def test_ai_engine():
    """Test the AI recommendation engine with sample data"""
    print("🤖 Testing AI Recommendation Engine...")
    
    try:
        # Test with facility ID 29 (Murray Highland)
        facility_id = 29
        print(f"Testing with facility ID: {facility_id}")
        
        # Initialize the AI engine
        ai_engine = AIShiftRecommendationEngine(facility_id)
        print("✅ AI Engine initialized successfully")
        
        # Load data for the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        print(f"Loading data from {start_date.date()} to {end_date.date()}")
        
        ai_engine.load_data((start_date, end_date))
        print("✅ Data loaded successfully")
        
        # Test ADL analysis
        print("\n📊 Analyzing ADL patterns...")
        adl_analysis = ai_engine.analyze_adl_patterns()
        print(f"✅ ADL analysis completed. Found {len(adl_analysis)} residents")
        
        if adl_analysis:
            print("\n📋 Sample resident analysis:")
            for resident_id, analysis in list(adl_analysis.items())[:3]:  # Show first 3
                print(f"  Resident: {analysis['name']}")
                print(f"    Care Hours: {analysis['total_care_hours']}")
                print(f"    Acuity Score: {analysis['acuity_score']}")
                print(f"    Care Intensity: {analysis['care_intensity']}")
                print()
        
        # Test staffing requirements calculation
        print("👥 Calculating staffing requirements...")
        target_date = datetime.now().date()
        staffing_reqs = ai_engine.calculate_staffing_requirements(target_date)
        print(f"✅ Staffing requirements calculated for {target_date}")
        
        if staffing_reqs:
            print("\n📋 Staffing requirements by shift:")
            for shift_type, reqs in staffing_reqs.items():
                print(f"  {shift_type.upper()}: {reqs['total_staff_recommended']} staff")
                print(f"    Care Hours: {reqs['total_care_hours']}")
                print(f"    Residents: {reqs['resident_count']}")
                print(f"    High Acuity: {reqs['high_acuity_count']}")
                print()
        
        # Test shift recommendations
        print("📅 Generating shift recommendations...")
        recommendations = ai_engine.recommend_optimal_shifts(target_date)
        print(f"✅ Generated {len(recommendations)} shift recommendations")
        
        if recommendations:
            print("\n📋 Sample recommendations:")
            for i, rec in enumerate(recommendations[:3]):  # Show first 3
                print(f"  {i+1}. {rec['shift_type'].upper()} Shift")
                print(f"     Staff Required: {rec['staff_required']}")
                print(f"     Care Hours: {rec['care_hours']}")
                print(f"     Confidence: {rec['confidence_score']}")
                print(f"     Reasoning: {rec['reasoning']}")
                print()
        
        # Test NEW shift template recommendations
        print("🏗️  Generating shift template recommendations...")
        shift_templates = ai_engine.generate_shift_template_recommendations(target_date)
        print(f"✅ Generated {len(shift_templates)} shift template recommendations")
        
        if shift_templates:
            print("\n📋 Shift Template Recommendations:")
            for i, rec in enumerate(shift_templates[:5]):  # Show first 5
                print(f"  {i+1}. {rec['day']} - {rec['shift_type'].upper()} Shift")
                print(f"     Time: {rec['start_time']} - {rec['end_time']} ({rec['duration_hours']}h)")
                print(f"     Staff Needed: {rec['staff_needed']}")
                print(f"     Care Hours Covered: {rec['care_hours_covered']}h")
                print(f"     Confidence: {rec['confidence_score']}%")
                print(f"     Reasoning: {rec['reasoning']}")
                print()
        
        # Test AI insights
        print("🧠 Generating AI insights...")
        insights = ai_engine.get_ai_insights()
        print("✅ AI insights generated successfully")
        
        if insights:
            print("\n📊 Facility Insights:")
            print(f"  Total Residents: {insights['total_residents']}")
            print(f"  Total Care Hours: {insights['total_care_hours']}")
            print(f"  Average Acuity: {insights['average_acuity_score']}")
            print(f"  Staffing Efficiency: {insights['staffing_efficiency_score']}")
            
            print("\n🎯 Care Intensity Distribution:")
            for intensity, count in insights['care_intensity_distribution'].items():
                print(f"  {intensity}: {count}")
            
            if insights['recommendations']:
                print("\n💡 AI Recommendations:")
                for rec in insights['recommendations']:
                    print(f"  • {rec}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI engine: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai_engine()
    if success:
        print("\n✅ AI Recommendation Engine is working correctly!")
    else:
        print("\n❌ AI Recommendation Engine has issues that need to be fixed.")
        sys.exit(1)
