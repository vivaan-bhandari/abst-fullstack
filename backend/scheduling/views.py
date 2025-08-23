from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import calendar

from .models import (
    Staff, ShiftTemplate, Shift, StaffAssignment, StaffAvailability,
    AIInsight, AIRecommendation
)
from .serializers import (
    StaffSerializer, ShiftTemplateSerializer, ShiftSerializer,
    StaffAssignmentSerializer, StaffAvailabilitySerializer,
    AIInsightSerializer, AIRecommendationSerializer,
    DashboardStatsSerializer
)
from users.permissions import HasFacilityAccess


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'status', 'facility']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    ordering_fields = ['last_name', 'first_name', 'hire_date', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        user = self.request.user
        # Check if user has facility access
        try:
            from users.models import FacilityAccess
            facility_access = FacilityAccess.objects.filter(user=user, status='approved').first()
            
            if facility_access:
                # If facility filter is provided, use it; otherwise use user's approved facilities
                facility_id = self.request.query_params.get('facility')
                if facility_id:
                    # Check if user has access to the requested facility
                    if FacilityAccess.objects.filter(user=user, facility_id=facility_id, status='approved').exists():
                        return Staff.objects.filter(facility_id=facility_id)
                    else:
                        return Staff.objects.none()
                else:
                    # Return staff from all facilities user has access to
                    user_facilities = FacilityAccess.objects.filter(user=user, status='approved').values_list('facility_id', flat=True)
                    return Staff.objects.filter(facility_id__in=user_facilities)
            else:
                return Staff.objects.none()
        except Exception:
            return Staff.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        # Get facility_id from the serializer data (sent by frontend)
        facility_id = serializer.validated_data.get('facility_id')
        if facility_id:
            from residents.models import Facility
            try:
                facility = Facility.objects.get(id=facility_id)
                serializer.save(facility=facility)
            except Facility.DoesNotExist:
                raise serializers.ValidationError("Invalid facility ID")
        else:
            # Fallback to user's facility if no facility_id provided
            if hasattr(user, 'facility_access'):
                serializer.save(facility=user.facility_access.facility)
            else:
                raise serializers.ValidationError("No facility specified and user has no default facility")
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get staff summary statistics for the current facility"""
        user = request.user
        if not hasattr(user, 'facility_access'):
            return Response({'error': 'No facility access'}, status=status.HTTP_403_FORBIDDEN)
        
        facility = user.facility_access.facility
        staff_queryset = Staff.objects.filter(facility=facility)
        
        summary = {
            'count': staff_queryset.count(),
            'active_count': staff_queryset.filter(status='active').count(),
            'inactive_count': staff_queryset.filter(status__in=['inactive', 'on_leave', 'terminated']).count(),
        }
        
        serializer = DashboardStatsSerializer(summary)
        return Response(serializer.data)


class ShiftTemplateViewSet(viewsets.ModelViewSet):
    queryset = ShiftTemplate.objects.all()
    serializer_class = ShiftTemplateSerializer
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['shift_type', 'is_active', 'facility']
    search_fields = ['template_name']
    ordering_fields = ['template_name', 'shift_type', 'start_time']
    ordering = ['shift_type', 'start_time']
    
    def get_queryset(self):
        user = self.request.user
        # Check if user has facility access
        try:
            from users.models import FacilityAccess
            facility_access = FacilityAccess.objects.filter(user=user, status='approved').first()
            
            if facility_access:
                # If facility filter is provided, use it; otherwise use user's approved facilities
                facility_id = self.request.query_params.get('facility')
                if facility_id:
                    # Check if user has access to the requested facility
                    if FacilityAccess.objects.filter(user=user, facility_id=facility_id, status='approved').exists():
                        return ShiftTemplate.objects.filter(facility_id=facility_id)
                    else:
                        return ShiftTemplate.objects.none()
                else:
                    # Return templates from all facilities user has access to
                    user_facilities = FacilityAccess.objects.filter(user=user, status='approved').values_list('facility_id', flat=True)
                    return ShiftTemplate.objects.filter(facility_id__in=user_facilities)
            else:
                return ShiftTemplate.objects.none()
        except Exception:
            return ShiftTemplate.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        # Get facility_id from the serializer data (sent by frontend)
        facility_id = serializer.validated_data.get('facility_id')
        if facility_id:
            from residents.models import Facility
            try:
                facility = Facility.objects.get(id=facility_id)
                serializer.save(facility=facility)
            except Facility.DoesNotExist:
                raise serializers.ValidationError("Invalid facility ID")
        else:
            # Fallback to user's facility if no facility_id provided
            if hasattr(user, 'facility_access'):
                serializer.save(facility=user.facility_access.facility)
            else:
                raise serializers.ValidationError("No facility specified and user has no default facility")
    
    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """Copy a shift template"""
        template = self.get_object()
        new_template = ShiftTemplate.objects.create(
            template_name=f"{template.template_name} (Copy)",
            shift_type=template.shift_type,
            start_time=template.start_time,
            end_time=template.end_time,
            duration=template.duration,
            required_staff=template.required_staff,
            is_active=False,  # Start as inactive
            facility=template.facility
        )
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['date', 'shift_template__shift_type', 'facility']
    search_fields = ['shift_template__template_name']
    ordering_fields = ['date', 'shift_template__start_time']
    ordering = ['-date', 'shift_template__start_time']
    
    def get_queryset(self):
        user = self.request.user
        # Check if user has facility access
        try:
            from users.models import FacilityAccess
            facility_access = FacilityAccess.objects.filter(user=user, status='approved').first()
            
            if facility_access:
                # If facility filter is provided, use it; otherwise use user's approved facilities
                facility_id = self.request.query_params.get('facility')
                if facility_id:
                    # Check if user has access to the requested facility
                    if FacilityAccess.objects.filter(user=user, facility_id=facility_id, status='approved').exists():
                        return Shift.objects.filter(facility_id=facility_id)
                    else:
                        return Shift.objects.none()
                else:
                    # Return shifts from all facilities user has access to
                    user_facilities = FacilityAccess.objects.filter(user=user, status='approved').values_list('facility_id', flat=True)
                    return Shift.objects.filter(facility_id__in=user_facilities)
            else:
                return Shift.objects.none()
        except Exception:
            return Shift.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        # Get facility_id from the serializer data (sent by frontend)
        facility_id = serializer.validated_data.get('facility_id')
        if facility_id:
            from residents.models import Facility
            try:
                facility = Facility.objects.get(id=facility_id)
                serializer.save(facility=facility)
            except Facility.DoesNotExist:
                raise serializers.ValidationError("Invalid facility ID")
        else:
            # Fallback to user's facility if no facility_id provided
            if hasattr(user, 'facility_access'):
                serializer.save(facility=user.facility_access.facility)
            else:
                raise serializers.ValidationError("No facility specified and user has no default facility")
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get shifts for a specific week"""
        week_start = request.query_params.get('week_start')
        if week_start:
            try:
                week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid week_start format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to current week
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        shifts = self.get_queryset().filter(
            date__gte=week_start,
            date__lte=week_end
        )
        
        serializer = self.get_serializer(shifts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def auto_fill(self, request):
        """Auto-fill staff assignments for a week"""
        week_start = request.data.get('week_start')
        if not week_start:
            return Response({'error': 'week_start is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid week_start format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        week_end = week_start + timedelta(days=6)
        
        # Get available staff and shifts for the week
        shifts = self.get_queryset().filter(date__gte=week_start, date__lte=week_end)
        staff = Staff.objects.filter(facility=request.user.facility_access.facility, status='active')
        
        # Simple auto-fill logic: assign staff to shifts based on availability
        assignments_created = 0
        for shift in shifts:
            if not StaffAssignment.objects.filter(shift=shift).exists():
                # Find available staff for this shift
                available_staff = staff.filter(
                    staffavailability__date=shift.date,
                    staffavailability__availability_status='available'
                ).first()
                
                if available_staff:
                    StaffAssignment.objects.create(
                        staff=available_staff,
                        shift=shift,
                        status='assigned'
                    )
                    assignments_created += 1
        
        return Response({
            'message': f'Auto-fill completed. {assignments_created} assignments created.',
            'assignments_created': assignments_created
        })
    
    @action(detail=False, methods=['post'])
    def clear_assignments(self, request):
        """Clear all staff assignments for a week"""
        week_start = request.data.get('week_start')
        if not week_start:
            return Response({'error': 'week_start is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid week_start format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        week_end = week_start + timedelta(days=6)
        
        # Get shifts for the week and delete their assignments
        shifts = self.get_queryset().filter(date__gte=week_start, date__lte=week_end)
        assignments_deleted = StaffAssignment.objects.filter(shift__in=shifts).delete()[0]
        
        return Response({
            'message': f'Cleared {assignments_deleted} assignments for the week.',
            'assignments_deleted': assignments_deleted
        })
    
    @action(detail=False, methods=['post'])
    def clear_shifts(self, request):
        """Clear all shifts for a week but maintain grid structure"""
        week_start = request.data.get('week_start')
        facility_id = request.data.get('facility')
        
        if not week_start:
            return Response({'error': 'week_start is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not facility_id:
            return Response({'error': 'facility is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from residents.models import Facility
            facility = Facility.objects.get(id=facility_id)
            week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        except Facility.DoesNotExist:
            return Response({'error': 'Facility not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid week_start date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        
        week_end_date = week_start_date + timedelta(days=6)
        
        # Delete existing shifts for the week
        existing_shifts = self.get_queryset().filter(
            facility=facility,
            date__gte=week_start_date,
            date__lte=week_end_date
        )
        shifts_deleted = existing_shifts.count()
        existing_shifts.delete()
        
        # Create empty placeholder shifts to maintain grid structure
        shift_types = ['day', 'swing', 'noc']
        shifts_created = 0
        
        # Get or create shift templates for each shift type
        shift_templates = {}
        for shift_type in shift_types:
            template, created = ShiftTemplate.objects.get_or_create(
                facility=facility,
                shift_type=shift_type,
                defaults={
                    'template_name': f'{shift_type.title()} Shift',
                    'start_time': '08:00' if shift_type == 'day' else '16:00' if shift_type == 'swing' else '00:00',
                    'end_time': '16:00' if shift_type == 'day' else '00:00' if shift_type == 'swing' else '08:00',
                    'duration': 8.0,
                    'required_staff': 0,  # Start with 0 staff
                    'is_active': True
                }
            )
            shift_templates[shift_type] = template
        
        # Create empty shifts for each day and shift type
        for i in range(7):
            current_date = week_start_date + timedelta(days=i)
            
            for shift_type in shift_types:
                shift = Shift.objects.create(
                    date=current_date,
                    shift_template=shift_templates[shift_type],
                    facility=facility,
                    required_staff_count=0,  # Empty shift
                    required_staff_role='cna'
                )
                shifts_created += 1
        
        return Response({
            'message': f'Cleared {shifts_deleted} shifts and created {shifts_created} empty placeholder shifts to maintain grid structure.',
            'shifts_deleted': shifts_deleted,
            'shifts_created': shifts_created,
            'week_start': week_start_date.isoformat(),
            'week_end': week_end_date.isoformat()
        })


class StaffAssignmentViewSet(viewsets.ModelViewSet):
    queryset = StaffAssignment.objects.all()
    serializer_class = StaffAssignmentSerializer
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'shift__facility', 'staff__role']
    search_fields = ['staff__first_name', 'staff__last_name', 'shift__shift_template__template_name']
    ordering_fields = ['assigned_at', 'shift__date']
    ordering = ['-assigned_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Superadmin and staff users can access all assignments
        if user.is_superuser or user.is_staff:
            facility_id = self.request.query_params.get('facility')
            if facility_id:
                return StaffAssignment.objects.filter(shift__facility_id=facility_id)
            return StaffAssignment.objects.all()
        
        # Regular users with facility access
        if hasattr(user, 'facility_access'):
            # If facility filter is provided, use it; otherwise use user's facility
            facility_id = self.request.query_params.get('facility')
            if facility_id:
                return StaffAssignment.objects.filter(shift__facility_id=facility_id)
            return StaffAssignment.objects.filter(shift__facility=user.facility_access.facility)
        
        return StaffAssignment.objects.none()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a staff assignment"""
        assignment = self.get_object()
        assignment.status = 'confirmed'
        assignment.save()
        
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a staff assignment"""
        assignment = self.get_object()
        assignment.status = 'cancelled'
        assignment.save()
        
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)


class StaffAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = StaffAvailability.objects.all()
    serializer_class = StaffAvailabilitySerializer
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['availability_status', 'date', 'facility', 'staff__role']
    search_fields = ['staff__first_name', 'staff__last_name']
    ordering_fields = ['date', 'staff__last_name']
    ordering = ['-date', 'staff__last_name']
    
    def get_queryset(self):
        user = self.request.user
        
        # Superadmin and staff users can access all availability
        if user.is_superuser or user.is_staff:
            facility_id = self.request.query_params.get('facility')
            if facility_id:
                return StaffAvailability.objects.filter(facility_id=facility_id)
            return StaffAvailability.objects.all()
        
        # Check if user has facility access
        try:
            from users.models import FacilityAccess
            facility_access = FacilityAccess.objects.filter(user=user, status='approved').first()
            
            if (facility_access):
                # If facility filter is provided, use it; otherwise use user's approved facilities
                facility_id = self.request.query_params.get('facility')
                if facility_id:
                    # Check if user has access to the requested facility
                    if FacilityAccess.objects.filter(user=user, facility_id=facility_id, status='approved').exists():
                        return StaffAvailability.objects.filter(facility_id=facility_id)
                    else:
                        return StaffAvailability.objects.none()
                else:
                    # Return availability from all facilities user has access to
                    user_facilities = FacilityAccess.objects.filter(user=user, status='approved').values_list('facility_id', flat=True)
                    return StaffAvailability.objects.filter(facility_id__in=user_facilities)
            else:
                return StaffAvailability.objects.none()
        except Exception:
            return StaffAvailability.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        # Get facility_id from the serializer data (sent by frontend)
        facility_id = serializer.validated_data.get('facility_id')
        if facility_id:
            from residents.models import Facility
            try:
                facility = Facility.objects.get(id=facility_id)
                serializer.save(facility=facility)
            except Facility.DoesNotExist:
                raise serializers.ValidationError("Invalid facility ID")
        else:
            # Fallback to user's facility if no facility_id provided
            if hasattr(user, 'facility_access'):
                serializer.save(facility=user.facility_access.facility)
            else:
                raise serializers.ValidationError("No facility specified and user has no default facility")
    
    def perform_update(self, serializer):
        user = self.request.user
        # Get facility_id from the serializer data (sent by frontend)
        facility_id = serializer.validated_data.get('facility_id')
        if facility_id:
            from residents.models import Facility
            try:
                facility = Facility.objects.get(id=facility_id)
                serializer.save(facility=facility)
            except Facility.DoesNotExist:
                raise serializers.ValidationError("Invalid facility ID")
        else:
            # Fallback to user's facility if no facility_id provided
            if hasattr(user, 'facility_access'):
                serializer.save(facility=user.facility_access.facility)
            else:
                raise serializers.ValidationError("No facility specified and user has no default facility")
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get availability for a specific week"""
        week_start = request.query_params.get('week_start')
        if week_start:
            try:
                week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid week_start format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to current week
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        availability = self.get_queryset().filter(
            date__gte=week_start,
            date__lte=week_end
        )
        
        serializer = self.get_serializer(availability, many=True)
        return Response(serializer.data)


class AIInsightViewSet(viewsets.ModelViewSet):
    queryset = AIInsight.objects.all()
    serializer_class = AIInsightSerializer
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date', 'facility']
    ordering_fields = ['date']
    ordering = ['-date']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'facility_access'):
            # If facility filter is provided, use it; otherwise use user's facility
            facility_id = self.request.query_params.get('facility')
            if facility_id:
                return AIInsight.objects.filter(facility_id=facility_id)
            return AIInsight.objects.filter(facility=user.facility_access.facility)
        return AIInsight.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        # Get facility_id from the serializer data (sent by frontend)
        facility_id = serializer.validated_data.get('facility_id')
        if facility_id:
            from residents.models import Facility
            try:
                facility = Facility.objects.get(id=facility_id)
                serializer.save(facility=facility)
            except Facility.DoesNotExist:
                raise serializers.ValidationError("Invalid facility ID")
        else:
            # Fallback to user's facility if no facility_id provided
            if hasattr(user, 'facility_access'):
                serializer.save(facility=user.facility_access.facility)
            else:
                raise serializers.ValidationError("No facility specified and user has no default facility")
    
    @action(detail=False, methods=['get'])
    def staffing_analysis(self, request):
        """Get staffing analysis for a specific date"""
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get facility from query params or user access
        facility_id = request.query_params.get('facility')
        if facility_id:
            try:
                from residents.models import Facility
                facility = Facility.objects.get(id=facility_id)
            except Facility.DoesNotExist:
                return Response({'error': 'Facility not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            facility = request.user.facility_access.facility
        
        # Get insights for the date
        try:
            insight = AIInsight.objects.get(facility=facility, date=target_date)
        except AIInsight.DoesNotExist:
            return Response({'error': 'No insights available for this date'}, status=status.HTTP_404_NOT_FOUND)
        
        # Calculate staffing needs based on insights
        total_residents = insight.total_residents
        total_care_hours = insight.total_care_hours
        avg_acuity = insight.avg_acuity_score
        
        # Simple staffing calculation
        base_staff_needed = max(2, int(total_care_hours / 8))  # At least 2 staff, then 1 per 8 hours
        acuity_multiplier = 1 + (avg_acuity - 3) * 0.2  # Adjust based on acuity
        recommended_staff = max(base_staff_needed, int(base_staff_needed * acuity_multiplier))
        
        analysis = {
            'date': target_date,
            'facility': facility.name,
            'total_residents': total_residents,
            'total_care_hours': total_care_hours,
            'avg_acuity_score': avg_acuity,
            'base_staff_needed': base_staff_needed,
            'acuity_multiplier': round(acuity_multiplier, 2),
            'recommended_staff': recommended_staff,
            'staffing_efficiency': insight.staffing_efficiency,
            'acuity_distribution': {
                'low': insight.low_acuity_count,
                'medium': insight.medium_acuity_count,
                'high': insight.high_acuity_count
            }
        }
        
        return Response(analysis)


class AIRecommendationViewSet(viewsets.ModelViewSet):
    queryset = AIRecommendation.objects.all()
    serializer_class = AIRecommendationSerializer
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['date', 'shift_type', 'facility', 'applied']
    ordering_fields = ['date', 'shift_type']
    ordering = ['-date', 'shift_type']
    
    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'facility_access'):
            # If facility filter is provided, use it; otherwise use user's facility
            facility_id = self.request.query_params.get('facility')
            if facility_id:
                return AIRecommendation.objects.filter(facility_id=facility_id)
            return AIRecommendation.objects.filter(facility=user.facility_access.facility)
        return AIRecommendation.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        # Get facility_id from the serializer data (sent by frontend)
        facility_id = serializer.validated_data.get('facility_id')
        if facility_id:
            from residents.models import Facility
            try:
                facility = Facility.objects.get(id=facility_id)
                serializer.save(facility=facility)
            except Facility.DoesNotExist:
                raise serializers.ValidationError("Invalid facility ID")
        else:
            # Fallback to user's facility if no facility_id provided
            if hasattr(user, 'facility_access'):
                serializer.save(facility=user.facility_access.facility)
            else:
                raise serializers.ValidationError("No facility specified and user has no default facility")
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Mark a recommendation as applied"""
        recommendation = self.get_object()
        recommendation.applied = True
        recommendation.save()
        
        serializer = self.get_serializer(recommendation)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def apply_recommendations(self, request):
        """Apply multiple recommendations at once"""
        recommendation_ids = request.data.get('recommendations', [])
        if not recommendation_ids:
            return Response({'error': 'No recommendations provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        recommendations = self.get_queryset().filter(id__in=recommendation_ids)
        applied_count = 0
        
        for recommendation in recommendations:
            recommendation.applied = True
            recommendation.save()
            applied_count += 1
        
        return Response({
            'message': f'Applied {applied_count} recommendations.',
            'applied_count': applied_count
        })
    
    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get recommendations for a specific week"""
        week_start = request.query_params.get('week_start')
        if week_start:
            try:
                week_start = datetime.strptime(week_start, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid week_start format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to current week
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        recommendations = self.get_queryset().filter(
            date__gte=week_start,
            date__lte=week_end
        )
        
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def calculate_from_adl(self, request):
        """Calculate AI recommendations based on actual ADL data for a facility"""
        facility_id = request.query_params.get('facility')
        week_start = request.query_params.get('week_start')
        
        if not facility_id:
            return Response({'error': 'facility parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from residents.models import Facility, FacilitySection, Resident
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            return Response({'error': 'Facility not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse week start date
        if week_start:
            try:
                week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid week_start format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            # Default to current week
            today = timezone.now().date()
            week_start_date = today - timedelta(days=today.weekday())
        
        week_end_date = week_start_date + timedelta(days=6)
        
        # Get all residents in the facility
        sections = FacilitySection.objects.filter(facility=facility)
        residents = Resident.objects.filter(facility_section__in=sections, is_deleted=False)
        
        # Check if there's actual facility data before generating recommendations
        if residents.count() == 0:
            return Response({
                'recommendations': [],
                'weekly_summary': {
                    'total_recommendations': 0,
                    'total_care_hours': 0,
                    'total_staff_required': 0,
                    'avg_confidence': 0
                },
                'care_intensity': {
                    'low_acuity_count': 0,
                    'medium_acuity_count': 0,
                    'high_acuity_count': 0
                },
                'facility': {
                    'id': facility.id,
                    'name': facility.name
                },
                'week_start': week_start_date.isoformat(),
                'week_end': week_end_date.isoformat(),
                'message': 'No residents found in this facility. AI recommendations require resident data.'
            })
        
        # Check if residents have shift time data
        residents_with_data = 0
        for resident in residents:
            if hasattr(resident, 'total_shift_times') and resident.total_shift_times:
                residents_with_data += 1
                # Debug: Show first resident's data structure
                if residents_with_data == 1:
                    print(f"🔍 DEBUG - First resident '{resident.name}' shift times: {resident.total_shift_times}")
        
        if residents_with_data == 0:
            return Response({
                'recommendations': [],
                'weekly_summary': {
                    'total_recommendations': 0,
                    'total_care_hours': 0,
                    'total_staff_required': 0,
                    'avg_confidence': 0
                },
                'care_intensity': {
                    'low_acuity_count': 0,
                    'medium_acuity_count': 0,
                    'high_acuity_count': 0
                },
                'facility': {
                    'id': facility.id,
                    'name': facility.name
                },
                'week_start': week_start_date.isoformat(),
                'week_end': week_end_date.isoformat(),
                'message': 'No shift time data found for residents. AI recommendations require resident care schedule data.'
            })
        
        # Calculate care hours per shift per day based on actual resident shift times
        recommendations = []
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        shift_types = ['day', 'swing', 'noc']
        
        # Map shift types to CSV column names
        shift_mapping = {
            'day': 1,      # Shift1
            'swing': 2,    # Shift2  
            'noc': 3       # Shift3
        }
        
        # Clear old AI recommendations for this week to avoid duplicates
        AIRecommendation.objects.filter(
            facility=facility,
            date__gte=week_start_date,
            date__lte=week_end_date
        ).delete()
        
        for i, day_name in enumerate(weekdays):
            current_date = week_start_date + timedelta(days=i)
            
            for shift_type in shift_types:
                # Calculate total care hours for this shift type on this day
                total_hours = 0
                
                # Map full day names to the prefixes used in resident.total_shift_times
                day_prefix_map = {
                    'Monday': 'Mon',
                    'Tuesday': 'Tues',  # Corrected prefix for Tuesday
                    'Wednesday': 'Wed',
                    'Thursday': 'Thurs', # Corrected prefix for Thursday
                    'Friday': 'Fri',
                    'Saturday': 'Sat',
                    'Sunday': 'Sun',
                }
                
                # Get the correct day prefix from the map
                day_prefix = day_prefix_map.get(day_name)
                if not day_prefix:
                    print(f"⚠️ WARNING - No day prefix found for {day_name}. Skipping.")
                    continue
                
                for resident in residents:
                    # Get shift times from resident.total_shift_times (this is where the actual hours are stored)
                    if hasattr(resident, 'total_shift_times') and resident.total_shift_times:
                        shift_num = shift_mapping[shift_type]
                        column_name = f'ResidentTotal{day_prefix}Shift{shift_num}Time'
                        
                        # Get the shift time in minutes from resident data
                        shift_minutes = resident.total_shift_times.get(column_name, 0)
                        if shift_minutes and shift_minutes > 0:
                            total_hours += float(shift_minutes) / 60  # Convert minutes to hours
                
                # Calculate staff required (8 hours per staff member, round up)
                staff_required = max(1, int((total_hours / 8) + 0.99)) if total_hours > 0 else 0
                
                # Debug: Print what we're calculating
                if total_hours > 0:
                    print(f"🔍 DEBUG - {day_name} {shift_type}: {total_hours}h -> {staff_required} staff")
                
                # Only add recommendation if there are care hours
                if total_hours > 0:
                    # Create and save AI recommendation to database
                    ai_recommendation = AIRecommendation.objects.create(
                        facility=facility,
                        date=current_date,
                        shift_type=shift_type,
                        care_hours=round(total_hours, 2),
                        required_staff=staff_required,
                        resident_count=residents.count(),
                        confidence=100,
                        applied=False
                    )
                    
                    recommendations.append({
                        'id': ai_recommendation.id,
                        'date': current_date.isoformat(),
                        'shift_type': shift_type,
                        'care_hours': round(total_hours, 2),
                        'required_staff': staff_required,
                        'resident_count': residents.count(),
                        'confidence': 100,  # High confidence since based on actual resident data
                        'facility_id': facility_id
                    })
        
        # Calculate weekly summary
        total_recommendations = len(recommendations)
        total_care_hours = sum(r['care_hours'] for r in recommendations)
        total_staff_required = sum(r['required_staff'] for r in recommendations)
        avg_confidence = 100 if total_recommendations > 0 else 0
        
        # Get facility insights for care intensity distribution
        try:
            from .models import AIInsight
            insight = AIInsight.objects.filter(facility=facility).order_by('-date').first()
            if insight:
                care_intensity = {
                    'low_acuity_count': insight.low_acuity_count,
                    'medium_acuity_count': insight.medium_acuity_count,
                    'high_acuity_count': insight.high_acuity_count
                }
            else:
                care_intensity = {
                    'low_acuity_count': 0,
                    'medium_acuity_count': 0,
                    'high_acuity_count': 0
                }
        except:
            care_intensity = {
                'low_acuity_count': 0,
                'medium_acuity_count': 0,
                'high_acuity_count': 0
            }
        
        return Response({
            'recommendations': recommendations,
            'weekly_summary': {
                'total_recommendations': total_recommendations,
                'total_care_hours': round(total_care_hours, 1),
                'total_staff_required': total_staff_required,
                'avg_confidence': avg_confidence
            },
            'care_intensity': care_intensity,
            'facility': {
                'id': facility.id,
                'name': facility.name
            },
            'week_start': week_start_date.isoformat(),
            'week_end': week_end_date.isoformat()
        })

    @action(detail=False, methods=['post'])
    def apply_weekly_recommendations(self, request):
        """Apply all AI recommendations for a week by creating shifts"""
        facility_id = request.data.get('facility')
        week_start = request.data.get('week_start')
        
        if not facility_id:
            return Response({'error': 'facility parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not week_start:
            return Response({'error': 'week_start parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from residents.models import Facility
            facility = Facility.objects.get(id=facility_id)
            week_start_date = datetime.strptime(week_start, '%Y-%m-%d').date()
        except Facility.DoesNotExist:
            return Response({'error': 'Facility not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid week_start date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        
        week_end_date = week_start_date + timedelta(days=6)
        
        # Get AI recommendations for this week
        recommendations = AIRecommendation.objects.filter(
            facility=facility,
            date__gte=week_start_date,
            date__lte=week_end_date
        )
        
        if not recommendations.exists():
            return Response({'error': 'No AI recommendations found for this week'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get or create shift templates for each shift type
        shift_templates = {}
        for shift_type in ['day', 'swing', 'noc']:
            template, created = ShiftTemplate.objects.get_or_create(
                facility=facility,
                shift_type=shift_type,
                defaults={
                    'template_name': f'{shift_type.title()} Shift',
                    'start_time': '08:00' if shift_type == 'day' else '16:00' if shift_type == 'swing' else '00:00',
                    'end_time': '16:00' if shift_type == 'day' else '00:00' if shift_type == 'swing' else '08:00',
                    'duration': 8.0,
                    'required_staff': 1,
                    'is_active': True
                }
            )
            shift_templates[shift_type] = template
        
        shifts_created = 0
        shifts_updated = 0
        
        for recommendation in recommendations:
            # Check if shift already exists for this date and shift type
            existing_shift = Shift.objects.filter(
                facility=facility,
                date=recommendation.date,
                shift_template__shift_type=recommendation.shift_type
            ).first()
            
            if existing_shift:
                # Update existing shift with new requirements
                existing_shift.required_staff_count = recommendation.required_staff
                existing_shift.save()
                shifts_updated += 1
                print(f"Updated shift: {existing_shift}")
            else:
                # Create new shift
                shift = Shift.objects.create(
                    date=recommendation.date,
                    shift_template=shift_templates[recommendation.shift_type],
                    facility=facility,
                    required_staff_count=recommendation.required_staff,
                    required_staff_role='cna'  # Default role
                )
                shifts_created += 1
                print(f"Created shift: {shift}")
            
            # Mark recommendation as applied
            recommendation.applied = True
            recommendation.save()
        
        return Response({
            'message': f'Successfully applied AI recommendations for {facility.name}',
            'shifts_created': shifts_created,
            'shifts_updated': shifts_updated,
            'total_recommendations': recommendations.count(),
            'week_start': week_start_date.isoformat(),
            'week_end': week_end_date.isoformat()
        })
    


        


        

        



class SchedulingDashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, HasFacilityAccess]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics for the current facility"""
        user = request.user
        if not hasattr(user, 'facility_access'):
            return Response({'error': 'No facility access'}, status=status.HTTP_403_FORBIDDEN)
        
        # If facility filter is provided, use it; otherwise use user's facility
        facility_id = request.query_params.get('facility')
        if facility_id:
            try:
                from residents.models import Facility
                facility = Facility.objects.get(id=facility_id)
            except Facility.DoesNotExist:
                return Response({'error': 'Facility not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            facility = user.facility_access.facility
        
        # Calculate statistics
        total_staff = Staff.objects.filter(facility=facility).count()
        total_shifts = Shift.objects.filter(facility=facility).count()
        total_assignments = StaffAssignment.objects.filter(shift__facility=facility).count()
        
        # Calculate understaffed shifts
        understaffed_shifts = 0
        shifts = Shift.objects.filter(facility=facility)
        for shift in shifts:
            required = shift.required_staff_count
            assigned = StaffAssignment.objects.filter(
                shift=shift, 
                status__in=['assigned', 'confirmed']
            ).count()
            if assigned < required:
                understaffed_shifts += 1
        
        # Calculate staffing efficiency (simplified)
        staffing_efficiency = 85.5  # This would be calculated based on actual business logic
        
        stats = {
            'total_staff': total_staff,
            'total_shifts': total_shifts,
            'total_assignments': total_assignments,
            'understaffed_shifts': understaffed_shifts,
            'staffing_efficiency': staffing_efficiency,
        }
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)
