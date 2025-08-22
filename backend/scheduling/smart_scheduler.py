import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from django.db.models import Q
import random

logger = logging.getLogger(__name__)

class SmartSchedulerAI:
    """
    AI-powered smart scheduler that generates optimal weekly schedules
    using local intelligence and data analysis
    """
    
    def __init__(self, facility_id: int):
        self.facility_id = facility_id
        self.staff_data = None
        self.shifts_data = None
        self.templates_data = None
        self.assignments_data = None
        
    def load_data(self):
        """Load all necessary data for smart scheduling"""
        try:
            from scheduling.models import Staff, Shift, ShiftTemplate, StaffAssignment, StaffAvailability
            
            # Load staff data with availability preferences
            staff_queryset = Staff.objects.filter(
                facility_id=self.facility_id,
                status='active'
            ).prefetch_related('availability')
            
            self.staff_data = []
            for staff in staff_queryset:
                staff_data = {
                    'id': staff.id,
                    'first_name': staff.first_name,
                    'last_name': staff.last_name,
                    'role': staff.role,
                    'skills': getattr(staff, 'skills', []),
                    'max_hours_per_week': getattr(staff, 'max_hours_per_week', 40),
                    'preferred_shifts': [],
                    'status': staff.status,
                    'availability_status': 'available',
                    'max_hours': 40
                }
                
                # Get availability preferences
                try:
                    availability = staff.availability.first()
                    if availability:
                        staff_data['preferred_shifts'] = availability.preferred_shifts or []
                        staff_data['availability_status'] = availability.availability_status
                        staff_data['max_hours'] = availability.max_hours or 40
                except:
                    pass
                
                self.staff_data.append(staff_data)
            
            # Load shift templates
            self.templates_data = list(ShiftTemplate.objects.filter(
                facility_id=self.facility_id,
                is_active=True
            ).values())
            
            # Load existing shifts
            self.shifts_data = list(Shift.objects.filter(
                facility_id=self.facility_id
            ).values())
            
            # Load existing assignments
            self.assignments_data = list(StaffAssignment.objects.filter(
                shift__facility_id=self.facility_id
            ).values('id', 'staff', 'shift', 'assigned_role'))
            
            logger.info(f"SmartScheduler loaded: {len(self.staff_data)} staff, {len(self.templates_data)} templates")
            
        except Exception as e:
            logger.error(f"Error loading data for smart scheduler: {e}")
            self.staff_data = []
            self.templates_data = []
            self.shifts_data = []
            self.assignments_data = []
    
    def generate_smart_week_schedule(self, target_date: datetime) -> Dict:
        """
        Generate an optimal weekly schedule using AI-like logic
        """
        try:
            print(f"DEBUG: Starting smart schedule generation for facility {self.facility_id}")
            self.load_data()
            print(f"DEBUG: Loaded {len(self.staff_data)} staff, {len(self.templates_data)} templates")
            
            # Get week dates
            week_dates = self._get_week_dates(target_date)
            print(f"DEBUG: Generated week dates: {[d.strftime('%Y-%m-%d') for d in week_dates]}")
            
            # Analyze current staffing situation
            analysis = self._analyze_staffing_needs(week_dates)
            print(f"DEBUG: Analysis complete, shift coverage: {analysis.get('shift_coverage', {})}")
            
            # Generate optimal schedule
            optimal_schedule = self._create_optimal_schedule(week_dates, analysis)
            print(f"DEBUG: Generated schedule with {len(optimal_schedule)} days")
            
            # Calculate confidence and reasoning
            confidence_score = self._calculate_schedule_confidence(optimal_schedule, analysis)
            print(f"DEBUG: Confidence score calculated: {confidence_score}")
            
            return {
                'success': True,
                'schedule': optimal_schedule,
                'confidence_score': confidence_score,
                'reasoning': self._generate_schedule_reasoning(optimal_schedule, analysis),
                'staff_utilization': self._calculate_staff_utilization(optimal_schedule),
                'conflict_resolution': self._resolve_scheduling_conflicts(optimal_schedule),
                'week_dates': [date.strftime('%Y-%m-%d') for date in week_dates]
            }
            
        except Exception as e:
            logger.error(f"Error generating smart schedule: {e}")
            return {
                'success': False,
                'error': str(e),
                'schedule': [],
                'confidence_score': 0
            }
    
    def _get_week_dates(self, target_date: datetime) -> List[datetime]:
        """Get Monday-Sunday dates for the target week"""
        # Find Monday of the target week
        days_ahead = target_date.weekday()
        monday = target_date - timedelta(days=days_ahead)
        
        week_dates = []
        for i in range(7):
            week_dates.append(monday + timedelta(days=i))
        
        return week_dates
    
    def _analyze_staffing_needs(self, week_dates: List[datetime]) -> Dict:
        """Analyze what staffing is needed for the week"""
        analysis = {
            'total_staff_needed': 0,
            'role_requirements': {},
            'shift_coverage': {},
            'staff_availability': {},
            'skill_gaps': [],
            'optimal_mix': {}
        }
        
        # Analyze shift templates to understand requirements
        for template in self.templates_data:
            shift_type = template.get('shift_type', 'day')
            required_staff = template.get('required_staff_count', 1)
            required_roles = template.get('required_roles', ['cna'])
            
            if shift_type not in analysis['shift_coverage']:
                analysis['shift_coverage'][shift_type] = 0
            analysis['shift_coverage'][shift_type] += required_staff * 7  # 7 days
            
            # Track role requirements
            for role in required_roles:
                if role not in analysis['role_requirements']:
                    analysis['role_requirements'][role] = 0
                analysis['role_requirements'][role] += required_staff * 7
        
        # Analyze staff availability and skills
        for staff in self.staff_data:
            staff_id = staff['id']
            role = staff['role']
            skills = staff.get('skills', [])
            max_hours = staff.get('max_hours_per_week', 40)
            
            analysis['staff_availability'][staff_id] = {
                'role': role,
                'skills': skills,
                'max_hours': max_hours,
                'current_hours': 0,
                'preferred_shifts': staff.get('preferred_shifts', []),
                'availability_score': self._calculate_availability_score(staff)
            }
        
        return analysis
    
    def _calculate_availability_score(self, staff: Dict) -> float:
        """Calculate how available a staff member is"""
        score = 100.0
        
        # Reduce score if they have many assignments
        current_assignments = len([a for a in self.assignments_data 
                                 if a.get('staff') == staff['id']])
        score -= current_assignments * 10
        
        # Boost score for preferred shifts
        if staff.get('preferred_shifts'):
            score += 20
        
        # Boost score for multiple skills
        if staff.get('skills') and len(staff['skills']) > 1:
            score += 15
        
        return max(0, min(100, score))
    
    def _calculate_shift_specific_score(self, staff: Dict, shift_type: str) -> float:
        """Calculate a score specific to the shift type for better staff assignment"""
        base_score = staff.get('availability_score', 0)
        
        # Boost score for shift preferences
        if staff.get('preferred_shifts') and shift_type in staff.get('preferred_shifts', []):
            base_score += 25
        
        # Reduce score for certain shift types based on staff characteristics
        if shift_type == 'noc':
            # Night shifts are harder - reduce score unless staff prefers them
            if 'noc' not in staff.get('preferred_shifts', []):
                base_score -= 15
            # Boost score for staff who might be night owls
            if staff.get('max_hours_per_week', 0) > 35:
                base_score += 10
        
        elif shift_type == 'swing':
            # Swing shifts are moderate - slight boost for experienced staff
            if staff.get('max_hours_per_week', 0) > 30:
                base_score += 5
        
        elif shift_type == 'day':
            # Day shifts are preferred by most - slight boost
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _create_optimal_schedule(self, week_dates: List[datetime], analysis: Dict) -> List[Dict]:
        """Create the optimal schedule using intelligent algorithms"""
        schedule = []
        
        # For each day of the week
        for date in week_dates:
            date_str = date.strftime('%Y-%m-%d')
            day_schedule = {
                'date': date_str,
                'day_name': date.strftime('%A'),
                'shifts': {}
            }
            
            # Track staff assignments for this day to prevent conflicts
            day_staff_assignments = set()
            
            # Process shifts in order of priority (Day -> Swing -> NOC)
            # This prevents one person from being assigned to multiple shifts on the same day
            shift_types = ['day', 'swing', 'noc']
            for shift_type in shift_types:
                shift_schedule = self._optimize_shift_staffing(
                    date, shift_type, analysis, day_staff_assignments
                )
                day_schedule['shifts'][shift_type] = shift_schedule
                
                # Add assigned staff to the day's assignment set to prevent conflicts
                for staff in shift_schedule.get('assigned_staff', []):
                    day_staff_assignments.add(staff['staff_id'])
            
            schedule.append(day_schedule)
        
        return schedule
    
    def _optimize_shift_staffing(self, date: datetime, shift_type: str, analysis: Dict, day_staff_assignments: set) -> Dict:
        """Optimize staff assignment for a specific shift"""
        # Find template for this shift type
        template = next((t for t in self.templates_data 
                        if t.get('shift_type') == shift_type), None)
        
        if not template:
            return {'status': 'no_template', 'assigned_staff': []}
        
        required_staff = template.get('required_staff_count', 1)
        required_roles = template.get('required_roles', ['cna'])
        
        # Get available staff for this shift (excluding those already assigned today)
        available_staff = self._get_available_staff_for_shift(
            date, shift_type, required_roles, analysis, day_staff_assignments
        )
        
        # Sort by availability score and shift preference
        available_staff.sort(key=lambda x: self._calculate_shift_specific_score(x, shift_type), reverse=True)
        
        assigned_staff = []
        for i in range(min(required_staff, len(available_staff))):
            staff_member = available_staff[i]
            assigned_staff.append({
                'staff_id': staff_member['id'],
                'name': f"{staff_member['first_name']} {staff_member['last_name']}",
                'role': staff_member['role'],
                'assignment_reason': self._generate_assignment_reason(staff_member, shift_type)
            })
            
            # Update availability score more aggressively for multiple shifts
            staff_member['availability_score'] -= 30
        
        return {
            'status': 'optimized',
            'template_name': template.get('name', 'Unknown'),
            'required_staff': required_staff,
            'assigned_staff': assigned_staff,
            'coverage_percentage': len(assigned_staff) / required_staff * 100
        }
    
    def _get_available_staff_for_shift(self, date: datetime, shift_type: str, 
                                      required_roles: List[str], analysis: Dict, day_staff_assignments: set) -> List[Dict]:
        """Get staff available for a specific shift"""
        available_staff = []
        
        for staff in self.staff_data:
            # Check if staff has required role
            if staff['role'] not in required_roles:
                continue
            
            # Check if staff is already assigned today (prevent same-day multiple shifts)
            if staff['id'] in day_staff_assignments:
                continue
            
            # Check if staff is available on this date
            if self._is_staff_available_on_date(staff['id'], date):
                # Check if staff has hours available
                current_hours = analysis['staff_availability'][staff['id']]['current_hours']
                max_hours = analysis['staff_availability'][staff['id']]['max_hours']
                
                if current_hours < max_hours:
                    staff_copy = staff.copy()
                    staff_copy['availability_score'] = analysis['staff_availability'][staff['id']]['availability_score']
                    available_staff.append(staff_copy)
        
        return available_staff
    
    def _is_staff_available_on_date(self, staff_id: int, date: datetime) -> bool:
        """Check if staff is already assigned on a specific date"""
        date_str = date.strftime('%Y-%m-%d')
        
        # Check existing assignments
        for assignment in self.assignments_data:
            if assignment.get('staff') == staff_id:
                # Check if this assignment is on the same date
                shift = next((s for s in self.shifts_data 
                            if s['id'] == assignment.get('shift')), None)
                if shift and shift.get('date') == date_str:
                    return False
        
        return True
    
    def _generate_assignment_reason(self, staff: Dict, shift_type: str) -> str:
        """Generate human-readable reason for staff assignment"""
        reasons = []
        
        # Role match
        reasons.append(f"Perfect {staff['role'].upper()} match")
        
        # Skill match
        if staff.get('skills'):
            reasons.append(f"Has required skills: {', '.join(staff['skills'])}")
        
        # Availability
        if staff.get('preferred_shifts') and shift_type in staff['preferred_shifts']:
            reasons.append("Prefers this shift type")
        
        # Experience
        if staff.get('max_hours_per_week', 0) > 30:
            reasons.append("Experienced staff member")
        
        return ". ".join(reasons) if reasons else "Best available match"
    
    def _calculate_schedule_confidence(self, schedule: List[Dict], analysis: Dict) -> int:
        """Calculate confidence score for the generated schedule"""
        if not schedule:
            return 0
        
        total_shifts = 0
        covered_shifts = 0
        staff_utilization = 0
        
        for day in schedule:
            for shift_type, shift_data in day['shifts'].items():
                if shift_data.get('status') == 'optimized':
                    total_shifts += 1
                    if shift_data.get('coverage_percentage', 0) >= 100:
                        covered_shifts += 1
                    
                    staff_utilization += shift_data.get('coverage_percentage', 0)
        
        if total_shifts == 0:
            return 0
        
        coverage_score = (covered_shifts / total_shifts) * 40
        utilization_score = (staff_utilization / total_shifts) * 30
        balance_score = self._calculate_balance_score(schedule) * 30
        
        confidence = min(100, max(0, int(coverage_score + utilization_score + balance_score)))
        
        return confidence
    
    def _calculate_balance_score(self, schedule: List[Dict]) -> float:
        """Calculate how well staff workload is balanced"""
        staff_hours = {}
        
        for day in schedule:
            for shift_type, shift_data in day['shifts'].items():
                if shift_data.get('status') == 'optimized':
                    for staff in shift_data.get('assigned_staff', []):
                        staff_id = staff['staff_id']
                        if staff_id not in staff_hours:
                            staff_hours[staff_id] = 0
                        staff_hours[staff_id] += 8  # Assume 8-hour shifts
        
        if not staff_hours:
            return 0
        
        # Calculate standard deviation of hours
        hours_list = list(staff_hours.values())
        mean_hours = sum(hours_list) / len(hours_list)
        
        variance = sum((h - mean_hours) ** 2 for h in hours_list) / len(hours_list)
        std_dev = variance ** 0.5
        
        # Lower standard deviation = better balance
        balance_score = max(0, 1 - (std_dev / mean_hours)) if mean_hours > 0 else 0
        
        return balance_score
    
    def _generate_schedule_reasoning(self, schedule: List[Dict], analysis: Dict) -> str:
        """Generate human-readable reasoning for the schedule"""
        reasoning_parts = []
        
        # Overall coverage
        total_shifts = sum(len(day['shifts']) for day in schedule)
        covered_shifts = sum(1 for day in schedule 
                           for shift_data in day['shifts'].values() 
                           if shift_data.get('coverage_percentage', 0) >= 100)
        
        reasoning_parts.append(f"Generated {total_shifts} shifts with {covered_shifts} fully covered")
        
        # Staff utilization
        total_staff = len(self.staff_data)
        assigned_staff = set()
        for day in schedule:
            for shift_data in day['shifts'].values():
                for staff in shift_data.get('assigned_staff', []):
                    assigned_staff.add(staff['staff_id'])
        
        utilization_rate = len(assigned_staff) / total_staff * 100 if total_staff > 0 else 0
        reasoning_parts.append(f"Utilized {utilization_rate:.1f}% of available staff")
        
        # Role coverage
        role_coverage = {}
        for day in schedule:
            for shift_data in day['shifts'].values():
                for staff in shift_data.get('assigned_staff', []):
                    role = staff['role']
                    if role not in role_coverage:
                        role_coverage[role] = 0
                    role_coverage[role] += 1
        
        if role_coverage:
            role_summary = ", ".join([f"{role}: {count}" for role, count in role_coverage.items()])
            reasoning_parts.append(f"Role distribution: {role_summary}")
        
        # Conflict resolution
        conflicts_resolved = self._count_resolved_conflicts(schedule)
        if conflicts_resolved > 0:
            reasoning_parts.append(f"Resolved {conflicts_resolved} potential scheduling conflicts")
        
        return ". ".join(reasoning_parts) + "."
    
    def _count_resolved_conflicts(self, schedule: List[Dict]) -> int:
        """Count how many conflicts were resolved in the schedule"""
        conflicts_resolved = 0
        
        # Check for double-booking
        staff_dates = {}
        for day in schedule:
            date = day['date']
            for shift_data in day['shifts'].values():
                for staff in shift_data.get('assigned_staff', []):
                    staff_id = staff['staff_id']
                    if staff_id not in staff_dates:
                        staff_dates[staff_id] = set()
                    
                    if date in staff_dates[staff_id]:
                        conflicts_resolved += 1
                    else:
                        staff_dates[staff_id].add(date)
        
        return conflicts_resolved
    
    def _calculate_staff_utilization(self, schedule: List[Dict]) -> Dict:
        """Calculate detailed staff utilization metrics"""
        utilization = {
            'total_staff': len(self.staff_data),
            'assigned_staff': 0,
            'utilization_rate': 0,
            'role_breakdown': {},
            'hours_distribution': {}
        }
        
        assigned_staff = set()
        role_counts = {}
        hours_per_staff = {}
        
        for day in schedule:
            for shift_data in day['shifts'].values():
                for staff in shift_data.get('assigned_staff', []):
                    staff_id = staff['staff_id']
                    role = staff['role']
                    
                    assigned_staff.add(staff_id)
                    
                    # Count by role
                    if role not in role_counts:
                        role_counts[role] = 0
                    role_counts[role] += 1
                    
                    # Count hours
                    if staff_id not in hours_per_staff:
                        hours_per_staff[staff_id] = 0
                    hours_per_staff[staff_id] += 8  # Assume 8-hour shifts
        
        utilization['assigned_staff'] = len(assigned_staff)
        utilization['utilization_rate'] = len(assigned_staff) / utilization['total_staff'] * 100
        utilization['role_breakdown'] = role_counts
        utilization['hours_distribution'] = hours_per_staff
        
        return utilization
    
    def _resolve_scheduling_conflicts(self, schedule: List[Dict]) -> List[Dict]:
        """Identify and resolve any remaining scheduling conflicts"""
        conflicts = []
        
        # Check for staff assigned to multiple shifts on same day
        staff_daily_assignments = {}
        
        for day in schedule:
            date = day['date']
            for shift_type, shift_data in day['shifts'].items():
                for staff in shift_data.get('assigned_staff', []):
                    staff_id = staff['staff_id']
                    
                    if staff_id not in staff_daily_assignments:
                        staff_daily_assignments[staff_id] = {}
                    
                    if date not in staff_daily_assignments[staff_id]:
                        staff_daily_assignments[staff_id][date] = []
                    
                    staff_daily_assignments[staff_id][date].append({
                        'shift_type': shift_type,
                        'staff_name': staff['name']
                    })
        
        # Identify conflicts
        for staff_id, dates in staff_daily_assignments.items():
            for date, shifts in dates.items():
                if len(shifts) > 1:
                    conflicts.append({
                        'type': 'double_booking',
                        'staff_id': staff_id,
                        'date': date,
                        'shifts': shifts,
                        'resolution': 'Remove duplicate assignments'
                    })
        
        return conflicts
    
    def apply_smart_schedule(self, schedule_data) -> Dict:
        """
        Apply the AI-generated schedule to create actual shifts and staff assignments
        """
        try:
            from scheduling.models import Shift, StaffAssignment, ShiftTemplate
            
            # Load data first
            self.load_data()
            
            created_shifts = []
            created_assignments = []
            errors = []
            
            # Validate schedule_data
            if not schedule_data:
                return {
                    'success': False,
                    'error': 'No schedule data provided',
                    'created_shifts': 0,
                    'created_assignments': 0
                }
            
            # Ensure schedule_data is iterable
            if not hasattr(schedule_data, '__iter__'):
                return {
                    'success': False,
                    'error': 'Schedule data is not iterable',
                    'created_shifts': 0,
                    'created_assignments': 0
                }
            
            # Process each day in the schedule
            # schedule_data is the schedule array directly, not nested
            for day_data in schedule_data:
                date_str = day_data.get('date')
                day_name = day_data.get('day_name')
                
                if not date_str:
                    errors.append(f"Missing date for day: {day_name}")
                    continue
                
                # Process each shift type for this day
                for shift_type, shift_data in day_data.get('shifts', {}).items():
                    if shift_data.get('status') != 'optimized':
                        continue
                    
                    # Find the shift template
                    template = next((t for t in self.templates_data 
                                   if t.get('shift_type') == shift_type), None)
                    
                    if not template:
                        errors.append(f"No template found for {shift_type} shift on {date_str}")
                        continue
                    
                    try:
                        # Check if shift already exists
                        existing_shift = Shift.objects.filter(
                            date=date_str,
                            shift_template_id=template['id'],
                            facility_id=self.facility_id
                        ).first()
                        
                        if existing_shift:
                            # Shift exists, update it and clear existing assignments
                            shift = existing_shift
                            shift.notes = f"AI Generated Smart Schedule - {day_name} {shift_type.title()}"
                            shift.save()
                            
                            # Clear existing assignments for this shift
                            StaffAssignment.objects.filter(shift=shift).delete()
                            
                            # Note that we're updating existing shift
                            created_shifts.append(f"updated_{shift.id}")
                        else:
                            # Create new shift
                            shift = Shift.objects.create(
                                date=date_str,
                                shift_template_id=template['id'],
                                facility_id=self.facility_id,
                                status='scheduled',
                                notes=f"AI Generated Smart Schedule - {day_name} {shift_type.title()}"
                            )
                            created_shifts.append(shift.id)
                        
                        # Create staff assignments
                        for staff_data in shift_data.get('assigned_staff', []):
                            try:
                                assignment = StaffAssignment.objects.create(
                                    staff_id=staff_data['staff_id'],
                                    shift=shift,
                                    assigned_role=staff_data['role'],
                                    notes=f"AI Assignment: {staff_data['assignment_reason']}"
                                )
                                created_assignments.append(assignment.id)
                                
                            except Exception as e:
                                errors.append(f"Failed to create assignment for {staff_data['name']} on {date_str}: {str(e)}")
                        
                    except Exception as e:
                        errors.append(f"Failed to create/update {shift_type} shift on {date_str}: {str(e)}")
            
            # Count new vs updated shifts
            new_shifts = len([s for s in created_shifts if not str(s).startswith('updated_')])
            updated_shifts = len([s for s in created_shifts if str(s).startswith('updated_')])
            
            return {
                'success': len(errors) == 0,
                'created_shifts': new_shifts,
                'updated_shifts': updated_shifts,
                'created_assignments': len(created_assignments),
                'errors': errors,
                'message': f"Successfully processed {len(created_shifts)} shifts ({new_shifts} new, {updated_shifts} updated) and {len(created_assignments)} assignments"
            }
            
        except Exception as e:
            logger.error(f"Error applying smart schedule: {e}")
            return {
                'success': False,
                'error': str(e),
                'created_shifts': 0,
                'created_assignments': 0
            }
