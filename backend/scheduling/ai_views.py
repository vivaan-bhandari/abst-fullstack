from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta
from django_filters.rest_framework import DjangoFilterBackend
from .ai_recommendations import AIShiftRecommendationEngine
from .models import Staff, ShiftTemplate, Shift
from .serializers import StaffSerializer, ShiftTemplateSerializer, ShiftSerializer
from residents.models import Facility, FacilitySection
import logging
from .smart_scheduler import SmartSchedulerAI

logger = logging.getLogger(__name__)

class AIRecommendationViewSet(viewsets.ViewSet):
    """
    AI-powered shift recommendation endpoints
    """
    permission_classes = [IsAuthenticated]
    
    def get_facility_id(self, request):
        """Get facility ID from query params or user's facility access"""
        facility_id = request.query_params.get('facility')
        
        if not facility_id:
            # Get user's first approved facility
            from users.models import FacilityAccess
            facility_access = FacilityAccess.objects.filter(
                user=request.user,
                status='approved'
            ).first()
            
            if facility_access:
                facility_id = facility_access.facility_id
            else:
                return None
        
        return int(facility_id) if facility_id else None
    
    @action(detail=False, methods=['get'])
    def insights(self, request):
        """Get comprehensive AI insights for a facility"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get date range from query params
            days_back = int(request.query_params.get('days_back', 30))
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            
            try:
                ai_engine.load_data((start_date, end_date))
            except Exception as e:
                logger.error(f"Error loading data for AI insights: {e}")
                return Response(
                    {'error': 'Failed to load facility data for analysis'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get insights
            try:
                insights = ai_engine.get_ai_insights()
                if not insights:
                    insights = {
                        'facility_id': facility_id,
                        'total_residents': 0,
                        'total_care_hours': 0,
                        'average_acuity_score': 0,
                        'care_intensity_distribution': {'low': 0, 'medium': 0, 'high': 0},
                        'care_patterns': [],
                        'staffing_efficiency_score': 0.5,
                        'recommendations': ['No data available for analysis']
                    }
            except Exception as e:
                logger.error(f"Error generating AI insights: {e}")
                return Response(
                    {'error': 'Failed to generate AI insights'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response(insights)
            
        except Exception as e:
            logger.error(f"Error getting AI insights: {e}")
            return Response(
                {'error': 'Failed to generate AI insights'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def shift_recommendations(self, request):
        """Get AI-powered shift recommendations for a specific date"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get target date from query params
            target_date_str = request.query_params.get('date')
            if target_date_str:
                try:
                    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
                except ValueError:
                    return Response(
                        {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                target_date = timezone.now().date()
            
            # Get section ID if specified
            section_id = request.query_params.get('section')
            if section_id:
                section_id = int(section_id)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            
            # Load data for analysis (last 30 days)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            try:
                ai_engine.load_data((start_date, end_date))
            except Exception as e:
                logger.error(f"Error loading data for shift recommendations: {e}")
                return Response(
                    {'error': 'Failed to load facility data for analysis'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get recommendations
            try:
                recommendations = ai_engine.recommend_optimal_shifts(target_date, section_id)
                if recommendations is None:
                    recommendations = []
            except Exception as e:
                logger.error(f"Error generating shift recommendations: {e}")
                recommendations = []
            
            return Response({
                'facility_id': facility_id,
                'target_date': target_date.strftime('%Y-%m-%d'),
                'section_id': section_id,
                'recommendations': recommendations,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting shift recommendations: {e}")
            return Response(
                {'error': 'Failed to generate shift recommendations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def weekly_recommendations(self, request):
        """Get AI-powered weekly shift recommendations by day"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get section ID if specified
            section_id = request.query_params.get('section')
            if section_id:
                section_id = int(section_id)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            
            # Load data for analysis (last 30 days)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            
            try:
                ai_engine.load_data((start_date, end_date))
            except Exception as e:
                logger.error(f"Error loading data for weekly recommendations: {e}")
                return Response(
                    {'error': 'Failed to load facility data for analysis'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get weekly recommendations
            try:
                recommendations = ai_engine.recommend_shifts_for_week(
                    target_date=timezone.now(),
                    section_id=section_id
                )
                if recommendations is None:
                    recommendations = []
            except Exception as e:
                logger.error(f"Error generating weekly recommendations: {e}")
                recommendations = []
            
            return Response({
                'facility_id': facility_id,
                'section_id': section_id,
                'weekly_recommendations': recommendations,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting weekly recommendations: {e}")
            return Response(
                {'error': 'Failed to generate weekly recommendations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def shift_template_recommendations(self, request):
        """Get AI-generated shift template recommendations for the planner grid"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get target date from query params
            target_date_str = request.query_params.get('date')
            if target_date_str:
                try:
                    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
                except ValueError:
                    return Response(
                        {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                target_date = timezone.now().date()
            
            # Get section ID if specified
            section_id = request.query_params.get('section')
            if section_id:
                section_id = int(section_id)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            
            # Load data for analysis (last 30 days)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            ai_engine.load_data((start_date, end_date))
            
            # Get shift template recommendations
            shift_recommendations = ai_engine.generate_shift_template_recommendations(target_date, section_id)
            
            return Response({
                'facility_id': facility_id,
                'target_date': target_date.strftime('%Y-%m-%d'),
                'section_id': section_id,
                'shift_template_recommendations': shift_recommendations,
                'total_recommendations': len(shift_recommendations),
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting shift template recommendations: {e}")
            return Response(
                {'error': 'Failed to generate shift template recommendations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def staffing_requirements(self, request):
        """Get AI-calculated staffing requirements for a date/section"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get target date from query params
            target_date_str = request.query_params.get('date')
            if target_date_str:
                try:
                    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
                except ValueError:
                    return Response(
                        {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                target_date = timezone.now().date()
            
            # Get section ID if specified
            section_id = request.query_params.get('section')
            if section_id:
                section_id = int(section_id)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            
            # Load data for analysis (last 30 days)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            ai_engine.load_data((start_date, end_date))
            
            # Get staffing requirements
            staffing_reqs = ai_engine.calculate_staffing_requirements(target_date, section_id)
            
            return Response({
                'facility_id': facility_id,
                'target_date': target_date.strftime('%Y-%m-%d'),
                'section_id': section_id,
                'staffing_requirements': staffing_reqs,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting staffing requirements: {e}")
            return Response(
                {'error': 'Failed to calculate staffing requirements'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def adl_analysis(self, request):
        """Get detailed ADL analysis for AI insights"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get date range from query params
            days_back = int(request.query_params.get('days_back', 30))
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            ai_engine.load_data((start_date, end_date))
            
            # Get ADL analysis
            adl_analysis = ai_engine.analyze_adl_patterns()
            
            return Response({
                'facility_id': facility_id,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'resident_analysis': adl_analysis,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting ADL analysis: {e}")
            return Response(
                {'error': 'Failed to analyze ADL data'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def apply_recommendations(self, request):
        """Apply AI recommendations to create shifts automatically"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get target date from request data
            target_date_str = request.data.get('date')
            if not target_date_str:
                return Response(
                    {'error': 'Target date is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get section ID if specified
            section_id = request.data.get('section')
            if section_id:
                section_id = int(section_id)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            
            # Load data for analysis (last 30 days)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            ai_engine.load_data((start_date, end_date))
            
            # Get recommendations
            recommendations = ai_engine.recommend_optimal_shifts(target_date, section_id)
            
            if not recommendations:
                return Response(
                    {'error': 'No recommendations available for the specified criteria'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create shifts based on recommendations
            created_shifts = []
            errors = []
            
            for rec in recommendations:
                try:
                    # Check if shift already exists
                    existing_shift = Shift.objects.filter(
                        date=target_date,
                        shift_template_id=rec['template_id'],
                        facility_id=facility_id
                    ).first()
                    
                    if existing_shift:
                        errors.append(f"Shift already exists for {rec['shift_type']} on {target_date_str}")
                        continue
                    
                    # Create new shift
                    shift = Shift.objects.create(
                        date=target_date,
                        shift_template_id=rec['template_id'],
                        facility_id=facility_id,
                        notes=f"AI Generated: {rec['reasoning']}"
                    )
                    
                    created_shifts.append({
                        'id': shift.id,
                        'shift_type': rec['shift_type'],
                        'staff_required': rec['staff_required'],
                        'reasoning': rec['reasoning']
                    })
                    
                except Exception as e:
                    errors.append(f"Failed to create {rec['shift_type']} shift: {str(e)}")
            
            return Response({
                'facility_id': facility_id,
                'target_date': target_date_str,
                'section_id': section_id,
                'created_shifts': created_shifts,
                'errors': errors,
                'success_count': len(created_shifts),
                'error_count': len(errors),
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error applying AI recommendations: {e}")
            return Response(
                {'error': 'Failed to apply AI recommendations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def apply_weekly_recommendations(self, request):
        """Apply AI weekly recommendations to create shifts for the entire week"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get target date from request data
            target_date_str = request.data.get('target_date')
            if not target_date_str:
                return Response(
                    {'error': 'Target date is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get section ID if specified
            section_id = request.data.get('section')
            if section_id:
                section_id = int(section_id)
            
            # Initialize AI engine
            ai_engine = AIShiftRecommendationEngine(facility_id)
            
            # Load data for analysis (last 30 days)
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30)
            ai_engine.load_data((start_date, end_date))
            
            # Get weekly recommendations
            weekly_recommendations = ai_engine.generate_shift_template_recommendations(target_date, section_id)
            
            if not weekly_recommendations:
                return Response(
                    {'error': 'No weekly shift template recommendations available for the specified criteria'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create shifts for the entire week based on shift template recommendations
            created_shifts = []
            errors = []
            
            # Calculate the start of the week (Monday) from target date
            target_weekday = target_date.weekday()  # 0=Monday, 6=Sunday
            week_start = target_date - timedelta(days=target_weekday)
            
            # Map day names to dates
            day_to_date = {
                'Monday': week_start,
                'Tuesday': week_start + timedelta(days=1),
                'Wednesday': week_start + timedelta(days=2),
                'Thursday': week_start + timedelta(days=3),
                'Friday': week_start + timedelta(days=4),
                'Saturday': week_start + timedelta(days=5),
                'Sunday': week_start + timedelta(days=6)
            }
            
            for rec in weekly_recommendations:
                day_name = rec.get('day')
                shift_type = rec.get('shift_type')
                
                if not day_name or not shift_type:
                    continue
                
                # Get the actual date for this day
                day_date = day_to_date.get(day_name)
                if not day_date:
                    continue
                
                try:
                    # Find appropriate shift template
                    shift_template = ShiftTemplate.objects.filter(
                        facility_id=facility_id,
                        shift_type__iexact=shift_type
                    ).first()
                    
                    if not shift_template:
                        errors.append(f"No shift template found for {shift_type} shift")
                        continue
                    
                    # Check if shift already exists
                    existing_shift = Shift.objects.filter(
                        date=day_date,
                        shift_template_id=shift_template.id,
                        facility_id=facility_id
                    ).first()
                    
                    if existing_shift:
                        errors.append(f"Shift already exists for {shift_type} on {day_date.strftime('%Y-%m-%d')}")
                        continue
                    
                    # Create new shift with proper staff count
                    shift = Shift.objects.create(
                        date=day_date,
                        shift_template_id=shift_template.id,
                        facility_id=facility_id,
                        notes=f"AI Generated (Weekly): {rec.get('reasoning', '')} - Staff needed: {rec.get('staff_needed', 1)}"
                    )
                    
                    # Create AcuityBasedStaffing record to override the default staff count
                    from .models import AcuityBasedStaffing
                    AcuityBasedStaffing.objects.create(
                        shift=shift,
                        total_care_hours_needed=rec.get('care_hours_covered', 0),
                        recommended_staff_count=rec.get('staff_needed', 1),
                        recommended_skill_mix={'cna': rec.get('staff_needed', 1)},  # Default to CNA for now
                        high_acuity_residents=0,  # Could be enhanced with actual acuity data
                        medium_acuity_residents=0,
                        low_acuity_residents=rec.get('resident_count', 0)
                    )
                    
                    created_shifts.append({
                        'id': shift.id,
                        'date': day_date.strftime('%Y-%m-%d'),
                        'shift_type': shift_type,
                        'start_time': rec.get('start_time', ''),
                        'end_time': rec.get('end_time', ''),
                        'staff_needed': rec.get('staff_needed', 1),
                        'care_hours_covered': rec.get('care_hours_covered', 0),
                        'reasoning': rec.get('reasoning', '')
                    })
                    
                except Exception as e:
                    errors.append(f"Failed to create {shift_type} shift for {day_name}: {str(e)}")
            
            return Response({
                'facility_id': facility_id,
                'target_date': target_date_str,
                'section_id': section_id,
                'created_shifts': created_shifts,
                'errors': errors,
                'success_count': len(created_shifts),
                'error_count': len(errors),
                'generated_at': timezone.now().isoformat(),
                'weekly': True
            })
            
        except Exception as e:
            logger.error(f"Error applying weekly AI recommendations: {e}")
            return Response(
                {'error': 'Failed to apply weekly AI recommendations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def facility_sections(self, request):
        """Get available facility sections for AI analysis"""
        try:
            facility_id = self.get_facility_id(request)
            if not facility_id:
                return Response(
                    {'error': 'No facility specified or access denied'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                sections = FacilitySection.objects.filter(
                    facility_id=facility_id
                ).values('id', 'name', 'description')
                
                sections_list = list(sections)
            except Exception as e:
                logger.error(f"Error querying facility sections: {e}")
                sections_list = []
            
            return Response({
                'facility_id': facility_id,
                'sections': sections_list
            })
            
        except Exception as e:
            logger.error(f"Error getting facility sections: {e}")
            return Response(
                {'error': 'Failed to get facility sections'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_smart_schedule(request):
    """
    Generate an AI-powered optimal weekly schedule
    """
    try:
        facility_id = request.data.get('facility_id')
        target_date_str = request.data.get('target_date')
        
        if not facility_id:
            return Response(
                {'error': 'facility_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not target_date_str:
            target_date = datetime.now()
        else:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Initialize the smart scheduler
        scheduler = SmartSchedulerAI(facility_id)
        
        # Generate the optimal schedule
        result = scheduler.generate_smart_week_schedule(target_date)
        
        if result['success']:
            return Response({
                'success': True,
                'message': 'Smart schedule generated successfully!',
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Failed to generate smart schedule',
                'details': result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error generating smart schedule: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_smart_schedule(request):
    """
    Apply the AI-generated smart schedule to create actual shifts and assignments
    """
    try:
        facility_id = request.data.get('facility_id')
        schedule_data = request.data.get('schedule')
        
        if not facility_id:
            return Response(
                {'error': 'facility_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not schedule_data:
            return Response(
                {'error': 'schedule data is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize the smart scheduler
        scheduler = SmartSchedulerAI(facility_id)
        
        # Apply the schedule to create actual shifts and assignments
        result = scheduler.apply_smart_schedule(schedule_data)
        
        if result['success']:
            return Response({
                'success': True,
                'message': 'Smart schedule applied successfully!',
                'data': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': 'Failed to apply smart schedule',
                'details': result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error applying smart schedule: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_scheduler(request):
    """
    Chat with the scheduling assistant
    """
    try:
        facility_id = request.data.get('facility_id')
        message = request.data.get('message')
        
        if not facility_id:
            return Response(
                {'error': 'facility_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not message:
            return Response(
                {'error': 'message is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import and initialize the chat processor
        from .chat_processor import SchedulingChatProcessor
        chat_processor = SchedulingChatProcessor(facility_id)
        
        # Process the message and get response
        response = chat_processor.process_message(message)
        
        return Response({
            'success': True,
            'response': response,
            'facility_id': facility_id
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Error in chat with scheduler: {e}")
        return Response(
            {'error': 'Internal server error'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
