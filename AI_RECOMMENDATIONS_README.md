# 🤖 AI-Powered Shift Recommendations System

## Overview

This system provides intelligent, data-driven shift recommendations based on ADL (Activities of Daily Living) data analysis. It uses machine learning algorithms to analyze care patterns, resident acuity levels, and historical data to suggest optimal staffing and shift schedules.

## 🚀 Features

### Core AI Capabilities
- **ADL Pattern Analysis**: Analyzes resident care patterns and identifies trends
- **Acuity Scoring**: Calculates resident acuity scores based on care complexity
- **Staffing Optimization**: Recommends optimal staff levels for each shift
- **Shift Timing**: Suggests optimal start/end times based on care patterns
- **Confidence Scoring**: Provides confidence levels for each recommendation

### Smart Insights
- **Care Intensity Distribution**: Categorizes residents by care needs (low/medium/high)
- **Staffing Efficiency**: Calculates overall facility staffing efficiency
- **Pattern Recognition**: Identifies common care patterns across residents
- **Predictive Recommendations**: Suggests improvements based on historical data

## 🏗️ Architecture

### Backend Components

#### 1. AI Recommendation Engine (`backend/scheduling/ai_recommendations.py`)
- **AIShiftRecommendationEngine**: Main AI engine class
- **Data Loading**: Loads ADL, staff, and shift template data
- **Pattern Analysis**: Analyzes care patterns and resident needs
- **Recommendation Generation**: Creates shift and staffing recommendations

#### 2. API Endpoints (`backend/scheduling/ai_views.py`)
- **AIRecommendationViewSet**: REST API for AI recommendations
- **Endpoints**:
  - `GET /insights/` - Get comprehensive AI insights
  - `GET /shift_recommendations/` - Get shift recommendations for a date
  - `GET /staffing_requirements/` - Get staffing requirements analysis
  - `GET /adl_analysis/` - Get detailed ADL analysis
  - `POST /apply_recommendations/` - Apply AI recommendations to create shifts
  - `GET /facility_sections/` - Get available facility sections

#### 3. URL Configuration
- Added to `backend/scheduling/urls.py`
- Accessible at `/api/scheduling/ai-recommendations/`

### Frontend Components

#### 1. AI Recommendations Component (`frontend/src/components/Scheduling/AIRecommendations.js`)
- **Modern React Component**: Built with Material-UI
- **Interactive Interface**: Date selection, section filtering, real-time analysis
- **Visual Insights**: Charts, progress bars, and intuitive displays
- **Action Buttons**: Apply recommendations, refresh analysis, detailed views

#### 2. Integration
- **New Tab**: Added to main scheduling interface
- **Seamless UX**: Integrates with existing scheduling workflow
- **Data Synchronization**: Updates parent components when recommendations are applied

## 🔧 Installation & Setup

### 1. Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

**Required Packages**:
- `numpy==1.24.3` - Numerical computing
- `pandas==2.3.0` - Data analysis and manipulation

### 2. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Test the AI Engine
```bash
cd backend
python test_ai_engine.py
```

## 📊 How It Works

### 1. Data Collection
The AI engine collects data from multiple sources:
- **ADL Records**: Resident care activities and time requirements
- **Staff Data**: Available staff, roles, and capacity
- **Shift Templates**: Existing shift patterns and requirements
- **Resident Information**: Demographics and care history

### 2. Pattern Analysis
```python
# Example: Analyzing resident care patterns
adl_analysis = ai_engine.analyze_adl_patterns()
for resident_id, analysis in adl_analysis.items():
    print(f"Resident: {analysis['name']}")
    print(f"Care Hours: {analysis['total_care_hours']}")
    print(f"Acuity Score: {analysis['acuity_score']}")
    print(f"Care Intensity: {analysis['care_intensity']}")
```

### 3. Acuity Scoring Algorithm
The system calculates resident acuity scores using:
- **Care Hours**: Total daily care requirements (40% weight)
- **Complexity**: Number of different ADL types (30% weight)
- **Frequency**: How often care is needed (30% weight)

```python
acuity_score = (hours_score * 0.4 + complexity_score * 0.3 + frequency_score * 0.3)
```

### 4. Staffing Calculations
```python
# Base staffing: 1 staff per 4 hours of care
base_staff = max(1, round(total_care_hours / 4.0))

# Acuity adjustment for high-need residents
acuity_adjustment = max(0, high_acuity_count - base_staff)

# Final recommendation
recommended_staff = base_staff + acuity_adjustment
```

### 5. Shift Recommendations
The system generates recommendations including:
- **Optimal Shift Times**: Based on when care is most needed
- **Staff Requirements**: Calculated for each shift type
- **Confidence Scores**: Reliability of each recommendation
- **AI Reasoning**: Human-readable explanation of recommendations

## 🎯 Usage Examples

### 1. Get AI Insights
```javascript
// Frontend API call
const response = await axios.get(
  `${API_BASE_URL}/api/scheduling/ai-recommendations/insights/?facility=${facilityId}&days_back=30`
);

// Response includes:
// - Total residents and care hours
// - Average acuity scores
// - Care intensity distribution
// - Staffing efficiency metrics
// - AI recommendations
```

### 2. Get Shift Recommendations
```javascript
// Get recommendations for a specific date
const response = await axios.get(
  `${API_BASE_URL}/api/scheduling/ai-recommendations/shift_recommendations/?facility=${facilityId}&date=2025-08-22`
);

// Each recommendation includes:
// - Shift type and timing
// - Staff requirements
// - Care hours and resident count
// - Confidence score and reasoning
```

### 3. Apply Recommendations
```javascript
// Automatically create shifts based on AI recommendations
const response = await axios.post(
  `${API_BASE_URL}/api/scheduling/ai-recommendations/apply_recommendations/?facility=${facilityId}`,
  {
    date: '2025-08-22',
    section: 1  // Optional: specific facility section
  }
);
```

## 🔍 API Reference

### Base URL
```
/api/scheduling/ai-recommendations/
```

### Endpoints

#### GET /insights/
**Parameters**:
- `facility` (required): Facility ID
- `days_back` (optional): Days of data to analyze (default: 30)

**Response**:
```json
{
  "facility_id": 29,
  "total_residents": 45,
  "total_care_hours": 180.5,
  "average_acuity_score": 6.2,
  "care_intensity_distribution": {
    "low": 15,
    "medium": 20,
    "high": 10
  },
  "staffing_efficiency_score": 0.85,
  "recommendations": [
    "Consider increasing staff during high-acuity periods",
    "High care requirements detected - review staffing ratios"
  ]
}
```

#### GET /shift_recommendations/
**Parameters**:
- `facility` (required): Facility ID
- `date` (optional): Target date (YYYY-MM-DD, default: today)
- `section` (optional): Facility section ID

**Response**:
```json
{
  "facility_id": 29,
  "target_date": "2025-08-22",
  "recommendations": [
    {
      "shift_type": "day",
      "template_id": 1,
      "template_name": "Day Shift",
      "recommended_start_time": "06:00",
      "recommended_end_time": "14:00",
      "staff_required": 3,
      "care_hours": 12.5,
      "resident_count": 45,
      "high_acuity_count": 3,
      "confidence_score": 0.85,
      "reasoning": "Based on 12.5 hours of care requirements. 3 high-acuity residents requiring intensive care."
    }
  ]
}
```

#### POST /apply_recommendations/
**Request Body**:
```json
{
  "date": "2025-08-22",
  "section": 1
}
```

**Response**:
```json
{
  "facility_id": 29,
  "target_date": "2025-08-22",
  "created_shifts": [
    {
      "id": 123,
      "shift_type": "day",
      "staff_required": 3,
      "reasoning": "Based on 12.5 hours of care requirements..."
    }
  ],
  "success_count": 1,
  "error_count": 0
}
```

## 🎨 Frontend Features

### 1. AI Insights Dashboard
- **Real-time Metrics**: Live updates of facility statistics
- **Visual Indicators**: Progress bars, color-coded chips, and charts
- **Interactive Elements**: Expandable sections and detailed views

### 2. Shift Recommendations
- **Date Selection**: Choose target dates for analysis
- **Section Filtering**: Analyze specific facility sections
- **Confidence Display**: Visual confidence indicators for each recommendation
- **One-Click Application**: Apply all recommendations with a single button

### 3. Staffing Analysis
- **Detailed Breakdown**: View staffing requirements by shift type
- **Acuity Adjustments**: See how high-acuity residents affect staffing
- **Visual Comparison**: Easy-to-understand staffing metrics

## 🧪 Testing

### Run the Test Script
```bash
cd backend
python test_ai_engine.py
```

### Expected Output
```
🤖 Testing AI Recommendation Engine...
✅ AI Engine initialized successfully
✅ Data loaded successfully
📊 Analyzing ADL patterns...
✅ ADL analysis completed. Found X residents
👥 Calculating staffing requirements...
✅ Staffing requirements calculated for 2025-08-22
📅 Generating shift recommendations...
✅ Generated X shift recommendations
🧠 Generating AI insights...
✅ AI insights generated successfully
🎉 All tests completed successfully!
```

## 🔧 Configuration

### Environment Variables
No additional environment variables required beyond standard Django configuration.

### Customization Options
The AI engine can be customized by modifying:
- **Acuity Scoring Weights**: Adjust the importance of different factors
- **Staffing Ratios**: Change the base staff-to-care-hours ratio
- **Confidence Thresholds**: Modify confidence score calculations
- **Pattern Recognition**: Enhance care pattern detection algorithms

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError: No module named 'numpy'`
**Solution**: Install required packages
```bash
pip install numpy pandas
```

#### 2. Data Loading Issues
**Problem**: No ADL data found
**Solution**: Ensure ADL records exist and are not soft-deleted
```sql
SELECT COUNT(*) FROM adls_adl WHERE is_deleted = FALSE;
```

#### 3. Performance Issues
**Problem**: Slow response times
**Solution**: 
- Reduce `days_back` parameter
- Add database indexes on frequently queried fields
- Consider caching for repeated requests

### Debug Mode
Enable detailed logging by setting Django's log level to DEBUG:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'scheduling.ai_recommendations': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 🔮 Future Enhancements

### Planned Features
1. **Machine Learning Models**: Train on historical data for better predictions
2. **Seasonal Adjustments**: Account for seasonal care pattern changes
3. **Staff Skill Matching**: Match staff skills to resident needs
4. **Predictive Analytics**: Forecast future staffing needs
5. **Integration APIs**: Connect with external scheduling systems

### Advanced Algorithms
- **Clustering Analysis**: Group residents by similar care patterns
- **Time Series Analysis**: Predict care needs throughout the day
- **Optimization Algorithms**: Find globally optimal staffing solutions
- **Risk Assessment**: Identify potential staffing shortages

## 📚 Additional Resources

### Documentation
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Pandas Documentation](https://pandas.pydata.org/)
- [NumPy Documentation](https://numpy.org/)

### Related Components
- [ADL Management System](../adls/)
- [Staff Scheduling](../scheduling/)
- [Resident Management](../residents/)

---

## 🎯 Quick Start

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Test the Engine**: `python test_ai_engine.py`
3. **Access the UI**: Navigate to the "AI Recommendations" tab
4. **Get Insights**: Click "Refresh AI Analysis"
5. **Apply Recommendations**: Use "Get Recommendations" and "Apply All"

The AI system will automatically analyze your facility's data and provide intelligent staffing recommendations! 🚀
