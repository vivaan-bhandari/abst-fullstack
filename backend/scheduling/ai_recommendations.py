import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Avg, Count, Q
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class AIShiftRecommendationEngine:
    """
    AI-powered engine for recommending optimal staffing based on ADL data analysis
    """
    
    def __init__(self, facility_id: int):
        self.facility_id = facility_id
        self.adl_data = None
        self.staff_data = None
        self.shift_templates = None
        self.resident_data = None
        
    def load_data(self, date_range: Tuple[datetime, datetime] = None):
        """Load all necessary data for analysis"""
        try:
            from adls.models import ADL
            from scheduling.models import Staff, ShiftTemplate, Shift
            from residents.models import Resident, FacilitySection
            
            # Load ADL data
            adl_query = ADL.objects.filter(
                resident__facility_section__facility_id=self.facility_id,
                is_deleted=False
            )
            
            if date_range:
                start_date, end_date = date_range
                adl_query = adl_query.filter(
                    created_at__range=(start_date, end_date)
                )
            
            # Only get fields that actually exist in the model
            adl_records = list(adl_query.values(
                'resident_id', 'question_text', 'total_hours', 'per_day_shift_times',
                'created_at', 'status'
            ))
            
            # Convert per_day_shift_times from JSON string to dict if needed
            for record in adl_records:
                if 'per_day_shift_times' in record and record['per_day_shift_times']:
                    if isinstance(record['per_day_shift_times'], str):
                        try:
                            import json
                            record['per_day_shift_times'] = json.loads(record['per_day_shift_times'])
                        except (json.JSONDecodeError, TypeError):
                            record['per_day_shift_times'] = {}
                    elif not isinstance(record['per_day_shift_times'], dict):
                        record['per_day_shift_times'] = {}
                else:
                    record['per_day_shift_times'] = {}
            
            self.adl_data = adl_records
            
            # Load staff data
            self.staff_data = list(Staff.objects.filter(
                facility_id=self.facility_id,
                status='active'
            ).values(
                'id', 'role', 'skills', 'max_hours_per_week', 'preferred_shifts'
            ))
            
            # Load shift templates
            self.shift_templates = list(ShiftTemplate.objects.filter(
                facility_id=self.facility_id,
                is_active=True
            ).values())
            
            # Load resident data
            self.resident_data = list(Resident.objects.filter(
                facility_section__facility_id=self.facility_id
            ).values('id', 'name', 'status', 'facility_section_id', 'total_shift_times'))
            
            # Parse JSON fields in resident data
            for resident in self.resident_data:
                if 'total_shift_times' in resident and resident['total_shift_times']:
                    if isinstance(resident['total_shift_times'], str):
                        try:
                            import json
                            resident['total_shift_times'] = json.loads(resident['total_shift_times'])
                        except (json.JSONDecodeError, TypeError):
                            resident['total_shift_times'] = {}
                    elif not isinstance(resident['total_shift_times'], dict):
                        resident['total_shift_times'] = {}
                else:
                    resident['total_shift_times'] = {}
            
            logger.info(f"Loaded {len(self.adl_data)} ADL records, {len(self.staff_data)} staff, {len(self.shift_templates)} shift templates")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            # Return empty data instead of raising
            self.adl_data = []
            self.staff_data = []
            self.shift_templates = []
            self.resident_data = []
    
    def analyze_adl_patterns(self) -> Dict:
        """Analyze ADL patterns to understand care requirements and distribution"""
        try:
            if not self.adl_data or not self.resident_data:
                logger.warning("No ADL or resident data available for analysis")
                return {}
            
            df = pd.DataFrame(self.adl_data)
            
            # Handle empty DataFrame
            if df.empty:
                return {}
            
            # Group by resident and analyze care patterns
            resident_analysis = {}
            
            for resident in self.resident_data:
                resident_id = resident['id']
                resident_adls = df[df['resident_id'] == resident_id]
                
                if len(resident_adls) == 0:
                    continue
                
                # Use resident.total_shift_times instead of ADL total_hours
                # This contains the real care hours calculated from the ADL data
                total_shift_times = resident.get('total_shift_times', {})
                
                # Calculate total care hours from total_shift_times
                total_care_hours = 0
                if isinstance(total_shift_times, dict):
                    for shift_key, minutes in total_shift_times.items():
                        if minutes and minutes > 0:
                            total_care_hours += minutes / 60.0  # Convert minutes to hours
                
                logger.debug(f"Resident {resident_id}: total_care_hours from total_shift_times = {total_care_hours}")
                
                # Analyze shift-time distribution
                shift_time_analysis = self._analyze_shift_time_distribution(resident_adls, total_shift_times)
                
                # Analyze daily care patterns
                daily_patterns = self._analyze_daily_care_patterns(resident_adls, total_shift_times)
                
                # Determine acuity level based on care requirements
                acuity_score = self._calculate_acuity_score(resident_adls, total_care_hours)
                
                resident_analysis[resident_id] = {
                    'name': resident['name'],
                    'total_care_hours': total_care_hours,
                    'acuity_score': acuity_score,
                    'shift_time_distribution': shift_time_analysis,
                    'daily_care_patterns': daily_patterns,
                    'care_intensity': self._categorize_care_intensity(acuity_score),
                    'section_id': resident['facility_section_id']
                }
            
            return resident_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing ADL patterns: {e}")
            return {}
    
    def _analyze_shift_time_distribution(self, resident_adls: pd.DataFrame, total_shift_times: Dict) -> Dict:
        """Analyze how care is distributed across different shift times"""
        shift_distribution = {'day': 0, 'swing': 0, 'noc': 0}
        
        try:
            # Use the resident's total_shift_times which contains the real care hours
            if isinstance(total_shift_times, dict):
                shift_mapping = {
                    'Shift1': 'day',
                    'Shift2': 'swing', 
                    'Shift3': 'noc'
                }
                
                for shift_key, minutes in total_shift_times.items():
                    if not minutes or minutes <= 0:
                        continue
                        
                    # Parse the shift type from the key (e.g., "MonShift1Time" -> "day")
                    shift_type = None
                    for shift_abbrev, shift_name in shift_mapping.items():
                        if shift_abbrev in shift_key:
                            shift_type = shift_name
                            break
                    
                    if shift_type:
                        hours = minutes / 60.0  # Convert minutes to hours
                        shift_distribution[shift_type] += hours
                        logger.debug(f"Added {hours:.2f} hours to {shift_type} shift (minutes: {minutes})")
                    else:
                        logger.warning(f"Could not parse shift type from key: {shift_key}")
            else:
                logger.warning(f"total_shift_times is not a dict: {type(total_shift_times)}")
                
        except Exception as e:
            logger.error(f"Error analyzing shift time distribution: {e}")
        
        return shift_distribution

    def _analyze_daily_care_patterns(self, resident_adls: pd.DataFrame, total_shift_times: Dict) -> Dict:
        """Analyze how care is distributed across different days of the week"""
        daily_patterns = {
            'Monday': {'day': 0, 'swing': 0, 'noc': 0},
            'Tuesday': {'day': 0, 'swing': 0, 'noc': 0},
            'Wednesday': {'day': 0, 'swing': 0, 'noc': 0},
            'Thursday': {'day': 0, 'swing': 0, 'noc': 0},
            'Friday': {'day': 0, 'swing': 0, 'noc': 0},
            'Saturday': {'day': 0, 'swing': 0, 'noc': 0},
            'Sunday': {'day': 0, 'swing': 0, 'noc': 0}
        }
        
        logger.info(f"Starting daily care patterns analysis using total_shift_times")
        
        try:
            # Use the resident's total_shift_times which contains the real care hours
            if isinstance(total_shift_times, dict):
                # Map the shift keys to our day/shift structure
                day_mapping = {
                    'Mon': 'Monday',
                    'Tues': 'Tuesday', 
                    'Wed': 'Wednesday',
                    'Thurs': 'Thursday',
                    'Fri': 'Friday',
                    'Sat': 'Saturday',
                    'Sun': 'Sunday'
                }
                
                shift_mapping = {
                    'Shift1': 'day',
                    'Shift2': 'swing', 
                    'Shift3': 'noc'
                }
                
                for shift_key, minutes in total_shift_times.items():
                    if not minutes or minutes <= 0:
                        continue
                        
                    # Parse the shift key (e.g., "MonShift1Time", "TuesShift2Time")
                    day = None
                    shift_type = None
                    
                    for abbrev, full_name in day_mapping.items():
                        if abbrev in shift_key:
                            day = full_name
                            break
                    
                    for shift_abbrev, shift_name in shift_mapping.items():
                        if shift_abbrev in shift_key:
                            shift_type = shift_name
                            break
                    
                    if day and shift_type:
                        hours = minutes / 60.0  # Convert minutes to hours
                        daily_patterns[day][shift_type] += hours
                        logger.debug(f"Added {hours:.2f} hours to {day} {shift_type} (minutes: {minutes})")
                    else:
                        logger.warning(f"Could not parse shift key: {shift_key}")
            else:
                logger.warning(f"total_shift_times is not a dict: {type(total_shift_times)}")
                            
        except Exception as e:
            logger.error(f"Error analyzing daily care patterns: {e}")
            import traceback
            traceback.print_exc()
        
        # Log the final daily patterns for debugging
        logger.info(f"Final daily care patterns: {daily_patterns}")
        
        return daily_patterns

    def generate_shift_template_recommendations(self, target_date: datetime, section_id: int = None) -> List[Dict]:
        """Generate shift template recommendations for the planner grid"""
        try:
            # Get ADL analysis for target residents
            adl_analysis = self.analyze_adl_patterns()
            
            # Filter by section if specified
            if section_id:
                adl_analysis = {
                    k: v for k, v in adl_analysis.items() 
                    if v['section_id'] == section_id
                }
            
            if not adl_analysis:
                logger.warning("No ADL analysis available for shift template recommendations")
                return []
            
            logger.info(f"Generating shift template recommendations for {len(adl_analysis)} residents")
            
            # Aggregate daily care patterns across all residents
            weekly_patterns = {
                'Monday': {'day': 0, 'swing': 0, 'noc': 0},
                'Tuesday': {'day': 0, 'swing': 0, 'noc': 0},
                'Wednesday': {'day': 0, 'swing': 0, 'noc': 0},
                'Thursday': {'day': 0, 'swing': 0, 'noc': 0},
                'Friday': {'day': 0, 'swing': 0, 'noc': 0},
                'Saturday': {'day': 0, 'swing': 0, 'noc': 0},
                'Sunday': {'day': 0, 'swing': 0, 'noc': 0}
            }
            
            # Aggregate care hours across all residents
            for resident_id, resident_analysis in adl_analysis.items():
                daily_patterns = resident_analysis.get('daily_care_patterns', {})
                for day, shifts in daily_patterns.items():
                    for shift_type, hours in shifts.items():
                        weekly_patterns[day][shift_type] += hours
            
            # Generate shift template recommendations
            shift_recommendations = []
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            # Standard shift times
            shift_times = {
                'day': {'start': '06:00', 'end': '14:00', 'duration': 8},
                'swing': {'start': '14:00', 'end': '22:00', 'duration': 8},
                'noc': {'start': '22:00', 'end': '06:00', 'duration': 8}
            }
            
            for day in days:
                day_patterns = weekly_patterns[day]
                
                for shift_type, care_hours in day_patterns.items():
                    if care_hours > 0:
                        # Calculate how many staff needed for this shift
                        # Each staff member works an 8-hour shift
                        # Staff can handle multiple residents simultaneously
                        staff_needed = max(1, round(care_hours / 8.0))
                        
                        # Create shift template recommendation
                        shift_rec = {
                            'day': day,
                            'shift_type': shift_type,
                            'start_time': shift_times[shift_type]['start'],
                            'end_time': shift_times[shift_type]['end'],
                            'duration_hours': shift_times[shift_type]['duration'],
                            'staff_needed': staff_needed,
                            'care_hours_covered': round(care_hours, 2),
                            'resident_count': len(adl_analysis),
                            'confidence_score': self._calculate_weekly_confidence(care_hours, len(adl_analysis)),
                            'reasoning': f"Need {staff_needed} staff for {care_hours:.1f}h care on {day} {shift_type} shift"
                        }
                        
                        shift_recommendations.append(shift_rec)
                        logger.info(f"Generated shift template: {day} {shift_type} - {staff_needed} staff for {care_hours:.1f}h care")
            
            # Sort by day and shift type
            shift_recommendations.sort(key=lambda x: (days.index(x['day']), ['day', 'swing', 'noc'].index(x['shift_type'])))
            
            logger.info(f"Generated {len(shift_recommendations)} shift template recommendations")
            return shift_recommendations
            
        except Exception as e:
            logger.error(f"Error generating shift template recommendations: {e}")
            import traceback
            traceback.print_exc()
            return []

    def recommend_shifts_for_week(self, target_date: datetime, section_id: int = None) -> List[Dict]:
        """Generate shift recommendations for each day of the week based on daily care patterns"""
        try:
            # Get ADL analysis for target residents
            adl_analysis = self.analyze_adl_patterns()
            
            # Filter by section if specified
            if section_id:
                adl_analysis = {
                    k: v for k, v in adl_analysis.items() 
                    if v['section_id'] == section_id
                }
            
            if not adl_analysis:
                logger.warning("No ADL analysis available for recommendations")
                return []
            
            logger.info(f"Generating weekly recommendations for {len(adl_analysis)} residents")
            
            # Aggregate daily care patterns across all residents
            weekly_patterns = {
                'Monday': {'day': 0, 'swing': 0, 'noc': 0},
                'Tuesday': {'day': 0, 'swing': 0, 'noc': 0},
                'Wednesday': {'day': 0, 'swing': 0, 'noc': 0},
                'Thursday': {'day': 0, 'swing': 0, 'noc': 0},
                'Friday': {'day': 0, 'swing': 0, 'noc': 0},
                'Saturday': {'day': 0, 'swing': 0, 'noc': 0},
                'Sunday': {'day': 0, 'swing': 0, 'noc': 0}
            }
            
            # Aggregate care hours across all residents
            for resident_id, resident_analysis in adl_analysis.items():
                daily_patterns = resident_analysis.get('daily_care_patterns', {})
                logger.debug(f"Resident {resident_id}: daily patterns = {daily_patterns}")
                
                for day, shifts in daily_patterns.items():
                    for shift_type, hours in shifts.items():
                        weekly_patterns[day][shift_type] += hours
            
            logger.info(f"Weekly patterns aggregated: {weekly_patterns}")
            
            # Generate recommendations for each day
            recommendations = []
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for day in days:
                day_patterns = weekly_patterns[day]
                total_care_hours = sum(day_patterns.values())
                
                logger.debug(f"Day {day}: total care hours = {total_care_hours}")
                
                if total_care_hours > 0:  # Only recommend shifts if there's care needed
                    for shift_type, care_hours in day_patterns.items():
                        if care_hours > 0:
                            # Calculate staffing needs based on care hours
                            # For memory care, staff can handle multiple residents simultaneously
                            # 1 staff member can typically handle 8-10 hours of care per shift
                            # This accounts for parallel care delivery and staff efficiency
                            base_staff = max(1, round(care_hours / 8.0))
                            
                            confidence_score = self._calculate_weekly_confidence(care_hours, len(adl_analysis))
                            recommendation = {
                                'day': day,
                                'shift_type': shift_type,
                                'care_hours': round(care_hours, 2),
                                'staff_required': base_staff,
                                'resident_count': len(adl_analysis),
                                'confidence_score': confidence_score,
                                'reasoning': f"Care hours: {care_hours}h for {len(adl_analysis)} residents on {day} {shift_type} shift (1 staff per 8h care)"
                            }
                            recommendations.append(recommendation)
                            logger.info(f"Generated recommendation: {day} {shift_type} - {care_hours}h care, {base_staff} staff, {confidence_score}% confidence")
                else:
                    logger.debug(f"Day {day}: No care hours, skipping recommendations")
            
            # Sort by care hours (highest first)
            recommendations.sort(key=lambda x: x['care_hours'], reverse=True)
            
            logger.info(f"Generated {len(recommendations)} weekly recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating weekly shift recommendations: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _calculate_acuity_score(self, resident_adls: pd.DataFrame, total_care_hours: float) -> float:
        """Calculate acuity score based on care complexity and hours"""
        try:
            # Base score from total care hours (0-10 scale)
            hours_score = min(total_care_hours / 8.0, 10.0)  # Normalize to 8-hour day
            
            # Complexity score based on number of different ADL types
            unique_adls = resident_adls['question_text'].nunique()
            complexity_score = min(unique_adls / 5.0, 5.0)  # Normalize to 5 ADL types
            
            # Frequency score based on how often care is needed
            avg_frequency = resident_adls['total_hours'].fillna(0).mean()
            frequency_score = min(avg_frequency / 2.0, 5.0)  # Normalize to 2 hours average
            
            # Calculate weighted average
            total_score = (hours_score * 0.4) + (complexity_score * 0.3) + (frequency_score * 0.3)
            return min(total_score, 10.0)  # Cap at 10
            
        except Exception as e:
            logger.error(f"Error calculating acuity score: {e}")
            return 5.0  # Return middle score on error
    
    def _categorize_care_intensity(self, acuity_score: float) -> str:
        """Categorize care intensity based on acuity score"""
        if acuity_score <= 3:
            return 'low'
        elif acuity_score <= 6:
            return 'medium'
        else:
            return 'high'
    
    def calculate_staffing_requirements(self, target_date: datetime, section_id: int = None) -> Dict:
        """Calculate optimal staffing requirements based on ADL analysis"""
        try:
            # Filter residents by section if specified
            target_residents = [
                r for r in self.resident_data 
                if section_id is None or r['facility_section_id'] == section_id
            ]
            
            if not target_residents:
                return {}
            
            # Get ADL analysis for target residents
            adl_analysis = self.analyze_adl_patterns()
            target_analysis = {
                k: v for k, v in adl_analysis.items() 
                if any(r['id'] == k for r in target_residents)
            }
            
            # Calculate total care requirements by shift
            shift_requirements = {'day': 0, 'swing': 0, 'noc': 0}
            total_residents = len(target_residents)
            
            for resident_id, analysis in target_analysis.items():
                shift_dist = analysis['shift_time_distribution']
                for shift_type, hours in shift_dist.items():
                    shift_requirements[shift_type] += hours
            
            # Calculate optimal staffing based on care requirements
            staffing_recommendations = {}
            
            for shift_type, total_hours in shift_requirements.items():
                # Base staffing: 1 staff per 8 hours of care (realistic for memory care)
                # Staff can handle multiple residents simultaneously and work efficiently
                # This accounts for parallel care delivery and staff multitasking
                base_staff = max(1, round(total_hours / 8.0))
                
                # Adjust based on resident count and acuity
                high_acuity_count = sum(
                    1 for analysis in target_analysis.values() 
                    if analysis['care_intensity'] == 'high'
                )
                
                # Additional staff for high acuity residents
                acuity_adjustment = max(0, high_acuity_count - base_staff)
                
                # Final recommendation
                recommended_staff = base_staff + acuity_adjustment
                
                staffing_recommendations[shift_type] = {
                    'total_care_hours': round(total_hours, 2),
                    'base_staff_required': base_staff,
                    'acuity_adjustment': acuity_adjustment,
                    'total_staff_recommended': recommended_staff,
                    'resident_count': total_residents,
                    'high_acuity_count': high_acuity_count
                }
            
            return staffing_recommendations
            
        except Exception as e:
            logger.error(f"Error calculating staffing requirements: {e}")
            return {}
    
    def recommend_optimal_shifts(self, target_date: datetime, section_id: int = None) -> List[Dict]:
        """Generate optimal shift recommendations based on AI analysis"""
        try:
            # Get staffing requirements
            staffing_reqs = self.calculate_staffing_requirements(target_date, section_id)
            
            if not staffing_reqs:
                return []
            
            recommendations = []
            
            for shift_type, reqs in staffing_reqs.items():
                # Find matching shift template
                template = next(
                    (t for t in self.shift_templates if t['shift_type'] == shift_type), 
                    None
                )
                
                if not template:
                    continue
                
                # Calculate optimal start time based on care patterns
                optimal_start = self._calculate_optimal_start_time(shift_type, section_id)
                
                recommendation = {
                    'shift_type': shift_type,
                    'template_id': template['id'],
                    'template_name': template['name'],
                    'recommended_start_time': optimal_start,
                    'recommended_end_time': self._calculate_end_time(optimal_start, template['duration_hours']),
                    'staff_required': reqs['total_staff_recommended'],
                    'care_hours': reqs['total_care_hours'],
                    'resident_count': reqs['resident_count'],
                    'high_acuity_count': reqs['high_acuity_count'],
                    'confidence_score': self._calculate_confidence_score(reqs),
                    'reasoning': self._generate_reasoning(reqs, shift_type)
                }
                
                recommendations.append(recommendation)
            
            # Sort by priority (high acuity shifts first)
            recommendations.sort(key=lambda x: x['high_acuity_count'], reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating shift recommendations: {e}")
            return []
    
    def _calculate_optimal_start_time(self, shift_type: str, section_id: int = None) -> str:
        """Calculate optimal start time based on care patterns"""
        # Default start times
        default_times = {
            'day': '06:00',
            'swing': '14:00',
            'noc': '22:00'
        }
        
        if not self.adl_data:
            return default_times.get(shift_type, '08:00')
        
        try:
            # Filter ADL data for target section
            section_residents = [
                r['id'] for r in self.resident_data 
                if section_id is None or r['facility_section_id'] == section_id
            ]
            
            section_adls = [
                adl for adl in self.adl_data 
                if adl['resident_id'] in section_residents
            ]
            
            if not section_adls:
                return default_times.get(shift_type, '08:00')
            
            # Analyze when care is most needed for this shift type
            shift_adls = []
            for adl in section_adls:
                per_day_shift_times = adl.get('per_day_shift_times', {})
                if isinstance(per_day_shift_times, dict) and shift_type in per_day_shift_times:
                    shift_adls.append(per_day_shift_times[shift_type])
            
            if not shift_adls:
                return default_times.get(shift_type, '08:00')
            
            # For now, return default time (could be enhanced with more sophisticated time analysis)
            return default_times.get(shift_type, '08:00')
            
        except Exception as e:
            logger.error(f"Error calculating optimal start time: {e}")
            return default_times.get(shift_type, '08:00')
    
    def _calculate_end_time(self, start_time: str, duration_hours: float) -> str:
        """Calculate end time based on start time and duration"""
        try:
            start_dt = datetime.strptime(start_time, '%H:%M')
            end_dt = start_dt + timedelta(hours=float(duration_hours))
            return end_dt.strftime('%H:%M')
        except:
            return '16:00'  # Default fallback
    
    def _calculate_weekly_confidence(self, care_hours: float, resident_count: int) -> int:
        """Calculate confidence score for weekly recommendations (0-100)"""
        try:
            # Base confidence starts at 60% for having data
            base_confidence = 60
            
            # Data quality factor: more residents = higher confidence
            resident_factor = min(resident_count / 20.0, 1.0) * 20  # Up to 20 points
            
            # Care hours factor: more hours = higher confidence (normalized to 8-hour shift)
            hours_factor = min(care_hours / 8.0, 1.0) * 20  # Up to 20 points
            
            # Calculate total confidence
            total_confidence = base_confidence + resident_factor + hours_factor
            
            # Ensure confidence is between 60-100%
            final_confidence = min(100, max(60, round(total_confidence)))
            
            logger.debug(f"Weekly confidence calculation: care_hours={care_hours}, residents={resident_count}, base={base_confidence}, resident_factor={resident_factor}, hours_factor={hours_factor}, total={total_confidence}, final={final_confidence}")
            
            return final_confidence
            
        except Exception as e:
            logger.error(f"Error calculating weekly confidence score: {e}")
            return 60  # Return base confidence on error
    
    def _calculate_confidence_score(self, reqs: Dict) -> float:
        """Calculate confidence score for the recommendation (0-1)"""
        try:
            # Base confidence starts at 0.6 (60%) for having data
            base_confidence = 0.6
            
            # Data quality factor: more residents = higher confidence
            data_quality = min(reqs['resident_count'] / 15.0, 1.0) * 0.2  # Up to 20 points
            
            # Care hours factor: more hours = higher confidence (normalized to 8-hour shift)
            care_consistency = min(reqs['total_care_hours'] / 8.0, 1.0) * 0.2  # Up to 20 points
            
            # Calculate total confidence
            total_confidence = base_confidence + data_quality + care_consistency
            
            # Ensure confidence is between 0.6-1.0 (60-100%)
            final_confidence = min(1.0, max(0.6, round(total_confidence, 2)))
            
            logger.debug(f"Confidence calculation: residents={reqs['resident_count']}, care_hours={reqs['total_care_hours']}, base={base_confidence}, data_quality={data_quality}, care_consistency={care_consistency}, total={total_confidence}, final={final_confidence}")
            
            return final_confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.6  # Return base confidence on error
    
    def _generate_reasoning(self, reqs: Dict, shift_type: str) -> str:
        """Generate human-readable reasoning for the recommendation"""
        reasoning_parts = []
        
        if reqs['total_care_hours'] > 0:
            reasoning_parts.append(f"Based on {reqs['total_care_hours']} hours of care requirements")
        
        if reqs['high_acuity_count'] > 0:
            reasoning_parts.append(f"{reqs['high_acuity_count']} high-acuity residents requiring intensive care")
        
        if reqs['resident_count'] > 0:
            reasoning_parts.append(f"Total of {reqs['resident_count']} residents in this section")
        
        if reqs['acuity_adjustment'] > 0:
            reasoning_parts.append(f"Additional staff recommended due to high care complexity")
        
        if not reasoning_parts:
            reasoning_parts.append("Standard staffing based on facility guidelines")
        
        return ". ".join(reasoning_parts) + "."
    
    def get_ai_insights(self, date_range: Tuple[datetime, datetime] = None) -> Dict:
        """Get comprehensive AI insights for the facility"""
        try:
            # Load data if not already loaded
            if not self.adl_data:
                self.load_data(date_range)
            
            # Get ADL analysis
            adl_analysis = self.analyze_adl_patterns()
            
            # Calculate overall facility metrics
            total_residents = len(self.resident_data)
            total_care_hours = sum(analysis['total_care_hours'] for analysis in adl_analysis.values())
            avg_acuity = np.mean([analysis['acuity_score'] for analysis in adl_analysis.values()]) if adl_analysis else 0
            
            # Identify care patterns
            care_patterns = self._identify_care_patterns(adl_analysis)
            
            insights = {
                'facility_id': self.facility_id,
                'total_residents': total_residents,
                'total_care_hours': round(total_care_hours, 2),
                'average_acuity_score': round(avg_acuity, 2),
                'care_intensity_distribution': {
                    'low': sum(1 for a in adl_analysis.values() if a['care_intensity'] == 'low'),
                    'medium': sum(1 for a in adl_analysis.values() if a['care_intensity'] == 'medium'),
                    'high': sum(1 for a in adl_analysis.values() if a['care_intensity'] == 'high')
                },
                'care_patterns': care_patterns,
                'staffing_efficiency_score': self._calculate_staffing_efficiency(),
                'recommendations': self._generate_general_recommendations(adl_analysis)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {}
    
    def _identify_care_patterns(self, adl_analysis: Dict) -> List[Dict]:
        """Identify common care patterns across residents"""
        patterns = []
        
        try:
            # Group by care intensity
            intensity_groups = {}
            for analysis in adl_analysis.values():
                intensity = analysis['care_intensity']
                if intensity not in intensity_groups:
                    intensity_groups[intensity] = []
                intensity_groups[intensity].append(analysis)
            
            for intensity, group in intensity_groups.items():
                if len(group) > 1:  # Only report patterns with multiple residents
                    avg_hours = np.mean([a['total_care_hours'] for a in group])
                    patterns.append({
                        'pattern_type': f'{intensity}_care_intensity',
                        'resident_count': len(group),
                        'average_care_hours': round(avg_hours, 2),
                        'description': f"{len(group)} residents require {intensity} intensity care averaging {round(avg_hours, 2)} hours daily"
                    })
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error identifying care patterns: {e}")
            return []
    
    def _calculate_staffing_efficiency(self) -> float:
        """Calculate overall staffing efficiency score (0-1)"""
        try:
            if not self.staff_data or not self.adl_data:
                return 0.5
            
            # Calculate total available staff hours
            total_available_hours = sum(staff['max_hours_per_week'] for staff in self.staff_data)
            
            # Calculate total required care hours (weekly)
            total_care_hours = sum(adl['total_hours'] for adl in self.adl_data) * 7  # Daily to weekly
            
            # Efficiency is the ratio of available hours to required hours
            # Optimal is around 1.2 (20% buffer for breaks, emergencies, etc.)
            efficiency = total_available_hours / (total_care_hours * 1.2) if total_care_hours > 0 else 1.0
            
            # Normalize to 0-1 range
            efficiency = max(0, min(1, efficiency))
            
            return round(efficiency, 2)
            
        except Exception as e:
            logger.error(f"Error calculating staffing efficiency: {e}")
            return 0.5
    
    def _generate_general_recommendations(self, adl_analysis: Dict) -> List[str]:
        """Generate general recommendations based on analysis"""
        recommendations = []
        
        try:
            # Analyze care distribution
            total_care_hours = sum(analysis['total_care_hours'] for analysis in adl_analysis.values())
            high_acuity_count = sum(1 for a in adl_analysis.values() if a['care_intensity'] == 'high')
            
            if high_acuity_count > len(adl_analysis) * 0.3:  # More than 30% high acuity
                recommendations.append("Consider increasing staff during high-acuity periods")
            
            if total_care_hours > len(adl_analysis) * 6:  # Average more than 6 hours per resident
                recommendations.append("High care requirements detected - review staffing ratios")
            
            # Check for shift imbalances
            shift_analysis = {'day': 0, 'swing': 0, 'noc': 0}
            for analysis in adl_analysis.values():
                for shift_type, hours in analysis['shift_time_distribution'].items():
                    shift_analysis[shift_type] += hours
            
            max_shift = max(shift_analysis.values())
            min_shift = min(shift_analysis.values())
            
            if max_shift > min_shift * 2:  # Significant imbalance
                recommendations.append("Consider redistributing care hours across shifts for better balance")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating general recommendations: {e}")
            return ["Unable to generate recommendations at this time"]
