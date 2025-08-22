from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import (
    Staff, ShiftTemplate, Shift, StaffAssignment, 
    AcuityBasedStaffing, StaffAvailability
)
from .serializers import (
    StaffSerializer, StaffDetailSerializer, StaffCreateSerializer, ShiftTemplateSerializer,
    ShiftTemplateCreateSerializer, ShiftSerializer, ShiftDetailSerializer, ShiftCreateSerializer, StaffAssignmentSerializer,
    AcuityBasedStaffingSerializer, StaffAvailabilitySerializer, StaffAvailabilityCreateSerializer, StaffAssignmentCreateSerializer
)

class FacilityAccessMixin:
    """Mixin to check facility access permissions"""
    
    def check_facility_access(self, facility_id):
        """Check if user has access to the specified facility"""
        if not facility_id:
            return False
            
        from users.models import FacilityAccess
        try:
            access = FacilityAccess.objects.get(
                user=self.request.user,
                facility_id=facility_id,
                status='approved'
            )
            return True
        except FacilityAccess.DoesNotExist:
            return False
    
    def get_queryset(self):
        """Filter queryset by facility and check access permissions"""
        queryset = super().get_queryset()
        facility_id = self.request.query_params.get('facility')
        
        if facility_id:
            # Check if user has access to this facility
            if not self.check_facility_access(facility_id):
                return queryset.none()  # Return empty queryset if no access
            queryset = queryset.filter(facility_id=facility_id)
        
        return queryset

class StaffViewSet(FacilityAccessMixin, viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'status', 'facility']
    search_fields = ['first_name', 'last_name', 'employee_id']
    ordering_fields = ['last_name', 'first_name']
    ordering = ['last_name', 'first_name']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter staff by facility and check access permissions"""
        queryset = Staff.objects.all()
        facility_id = self.request.query_params.get('facility')
        
        if facility_id:
            # Check if user has access to this facility
            if not self.check_facility_access(facility_id):
                return queryset.none()  # Return empty queryset if no access
            queryset = queryset.filter(facility_id=facility_id)
        
        return queryset

    def perform_create(self, serializer):
        """Automatically set facility from query parameters"""
        facility_id = self.request.query_params.get('facility')
        if not facility_id:
            raise serializers.ValidationError({"facility": "Facility ID is required in query parameters to create staff."})
        
        # Check if user has access to this facility
        if not self.check_facility_access(facility_id):
            raise serializers.ValidationError({"facility": "You don't have access to this facility."})
        
        from residents.models import Facility
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            raise serializers.ValidationError({"facility": "Invalid facility ID provided."})
        
        serializer.save(facility=facility)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffCreateSerializer
        elif self.action == 'retrieve':
            return StaffDetailSerializer
        return StaffSerializer

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Get staff member's schedule for a date range"""
        staff = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        assignments = StaffAssignment.objects.filter(staff=staff)
        if start_date:
            assignments = assignments.filter(shift__date__gte=start_date)
        if end_date:
            assignments = assignments.filter(shift__date__lte=end_date)
        
        serializer = StaffAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

class ShiftTemplateViewSet(FacilityAccessMixin, viewsets.ModelViewSet):
    queryset = ShiftTemplate.objects.all()
    serializer_class = ShiftTemplateSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['shift_type', 'facility', 'is_active']
    search_fields = ['name', 'facility__name']
    ordering_fields = ['name', 'start_time', 'duration_hours']
    ordering = ['start_time']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter shift templates by facility and check access permissions"""
        queryset = ShiftTemplate.objects.all()
        facility_id = self.request.query_params.get('facility')
        
        if facility_id:
            # Check if user has access to this facility
            if not self.check_facility_access(facility_id):
                return queryset.none()  # Return empty queryset if no access
            queryset = queryset.filter(facility_id=facility_id)
        
        # Filter by active status - only show active templates by default for list operations
        # unless explicitly requested to show all (for management purposes)
        # This ensures that when creating shifts, only active templates are available
        # For individual object operations (retrieve, update, delete), we don't filter by is_active
        if self.action == 'list':
            show_all = self.request.query_params.get('show_all', 'false').lower() == 'true'
            if not show_all:
                queryset = queryset.filter(is_active=True)
        
        return queryset

    def perform_create(self, serializer):
        """Automatically set facility from query parameters"""
        facility_id = self.request.query_params.get('facility')
        if not facility_id:
            raise serializers.ValidationError({"facility": "Facility ID is required in query parameters to create a shift template."})
        
        # Check if user has access to this facility
        if not self.check_facility_access(facility_id):
            raise serializers.ValidationError({"facility": "You don't have access to this facility."})
        
        from residents.models import Facility
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            raise serializers.ValidationError({"facility": "Invalid facility ID provided."})
        
        serializer.save(facility=facility)

    def perform_update(self, serializer):
        """Automatically set facility from query parameters when updating"""
        facility_id = self.request.query_params.get('facility')
        if not facility_id:
            raise serializers.ValidationError({"facility": "Facility ID is required in query parameters to update a shift template."})
        
        # Check if user has access to this facility
        if not self.check_facility_access(facility_id):
            raise serializers.ValidationError({"facility": "You don't have access to this facility."})
        
        from residents.models import Facility
        try:
            facility = Facility.objects.get(id=facility_id)
        except Facility.DoesNotExist:
            raise serializers.ValidationError({"facility": "Invalid facility ID provided."})
        
        serializer.save(facility=facility)

    def get_serializer_class(self):
        if self.action == 'create':
            return ShiftTemplateCreateSerializer
        return ShiftTemplateSerializer

class ShiftViewSet(FacilityAccessMixin, viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'facility', 'shift_template__shift_type', 'date']
    search_fields = ['facility__name', 'shift_template__name']
    ordering_fields = ['date', 'shift_template__start_time']
    ordering = ['-date', 'shift_template__start_time']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter shifts by facility and check access permissions"""
        queryset = Shift.objects.all()
        facility_id = self.request.query_params.get('facility')
        
        if facility_id:
            # Check if user has access to this facility
            if not self.check_facility_access(facility_id):
                return queryset.none()  # Return empty queryset if no access
            queryset = queryset.filter(facility_id=facility_id)
        
        return queryset

    def perform_create(self, serializer):
        """Automatically set facility from shift template"""
        shift_template_value = serializer.validated_data.get('shift_template')

        if not shift_template_value:
            raise serializers.ValidationError({"shift_template": "Shift template is required to create a shift."})

        # Accept either a ShiftTemplate instance (usual DRF behavior) or an integer ID
        template = None
        if isinstance(shift_template_value, ShiftTemplate):
            template = shift_template_value
        else:
            try:
                template = ShiftTemplate.objects.get(id=shift_template_value)
            except ShiftTemplate.DoesNotExist:
                raise serializers.ValidationError({"shift_template": "Invalid shift template provided."})

        # Check if user has access to the facility
        if not self.check_facility_access(template.facility.id):
            raise serializers.ValidationError({"facility": "You don't have access to this facility."})

        facility = template.facility
        serializer.save(facility=facility)

    def get_serializer_class(self):
        if self.action == 'create':
            return ShiftCreateSerializer
        elif self.action == 'retrieve':
            return ShiftDetailSerializer
        return ShiftSerializer

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Get shifts for calendar view"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        facility_id = request.query_params.get('facility')
        
        queryset = self.get_queryset()
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if facility_id:
            queryset = queryset.filter(facility_id=facility_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def understaffed(self, request):
        """Get shifts that are understaffed"""
        queryset = self.get_queryset().filter(status='scheduled')
        # Apply facility filtering if provided
        facility_id = request.query_params.get('facility')
        if facility_id:
            queryset = queryset.filter(facility_id=facility_id)
        understaffed_shifts = [shift for shift in queryset if shift.is_understaffed]
        serializer = self.get_serializer(understaffed_shifts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_staff(self, request, pk=None):
        """Assign staff to a shift"""
        shift = self.get_object()
        staff_id = request.data.get('staff_id')
        assigned_role = request.data.get('assigned_role')
        
        if not staff_id or not assigned_role:
            return Response(
                {'error': 'staff_id and assigned_role are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            staff = Staff.objects.get(id=staff_id)
            assignment = StaffAssignment.objects.create(
                staff=staff,
                shift=shift,
                assigned_role=assigned_role
            )
            serializer = StaffAssignmentSerializer(assignment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Staff.DoesNotExist:
            return Response(
                {'error': 'Staff not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class StaffAssignmentViewSet(FacilityAccessMixin, viewsets.ModelViewSet):
    queryset = StaffAssignment.objects.all()
    serializer_class = StaffAssignmentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['assigned_role', 'shift__status', 'shift__facility']
    search_fields = ['staff__first_name', 'staff__last_name', 'shift__facility__name']
    ordering_fields = ['shift__date', 'shift__shift_template__start_time']
    ordering = ['shift__date', 'shift__shift_template__start_time']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter assignments by facility and check access permissions"""
        queryset = StaffAssignment.objects.all()
        facility_id = self.request.query_params.get('facility')
        
        if facility_id:
            # Check if user has access to this facility
            if not self.check_facility_access(facility_id):
                return queryset.none()  # Return empty queryset if no access
            queryset = queryset.filter(shift__facility_id=facility_id)
        
        return queryset

    def perform_create(self, serializer):
        """Ensure facility context is maintained"""
        serializer.save()

    def get_serializer_class(self):
        if self.action == 'create':
            return StaffAssignmentCreateSerializer
        return StaffAssignmentSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to add logging"""
        print(f"Creating staff assignment with data: {request.data}")
        try:
            response = super().create(request, *args, **kwargs)
            print(f"Assignment created successfully: {response.data}")
            return response
        except Exception as e:
            print(f"Error creating assignment: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            raise

    @action(detail=True, methods=['post'])
    def clock_in(self, request, pk=None):
        """Clock in for a shift"""
        try:
            print(f"Clock in request for assignment {pk}")
            print(f"Request data: {request.data}")
            
            assignment = self.get_object()
            print(f"Assignment found: {assignment.id}")
            print(f"Current clock_in_time: {assignment.clock_in_time}")
            
            # Use provided time or current time
            clock_in_time = request.data.get('clock_in_time')
            if clock_in_time:
                print(f"Using provided clock_in_time: {clock_in_time}")
                # Parse the ISO string to datetime object
                try:
                    from dateutil import parser
                    assignment.clock_in_time = parser.isoparse(clock_in_time)
                except ImportError:
                    # Fallback to Django's timezone parsing
                    assignment.clock_in_time = timezone.datetime.fromisoformat(clock_in_time.replace('Z', '+00:00'))
            else:
                print(f"Using current time: {timezone.now()}")
                assignment.clock_in_time = timezone.now()
            
            assignment.save()
            print(f"Assignment saved successfully")
            
            serializer = self.get_serializer(assignment)
            return Response(serializer.data)
        except Exception as e:
            print(f"Error in clock_in: {e}")
            import traceback
            traceback.print_exc()
            raise

    @action(detail=True, methods=['post'])
    def clock_out(self, request, pk=None):
        """Clock out from a shift"""
        try:
            print(f"Clock out request for assignment {pk}")
            print(f"Request data: {request.data}")
            
            assignment = self.get_object()
            print(f"Assignment found: {assignment.id}")
            print(f"Current clock_in_time: {assignment.clock_in_time}")
            print(f"Current clock_out_time: {assignment.clock_out_time}")
            
            # Use provided time or current time
            clock_out_time = request.data.get('clock_out_time')
            if clock_out_time:
                print(f"Using provided clock_out_time: {clock_out_time}")
                # Parse the ISO string to datetime object
                try:
                    from dateutil import parser
                    assignment.clock_out_time = parser.isoparse(clock_out_time)
                except ImportError:
                    # Fallback to Django's timezone parsing
                    assignment.clock_out_time = timezone.datetime.fromisoformat(clock_out_time.replace('Z', '+00:00'))
            else:
                print(f"Using current time: {timezone.now()}")
                assignment.clock_out_time = timezone.now()
            
            # Calculate actual hours worked
            if assignment.clock_in_time and assignment.clock_out_time:
                duration = assignment.clock_out_time - assignment.clock_in_time
                assignment.actual_hours_worked = duration.total_seconds() / 3600
                print(f"Calculated hours worked: {assignment.actual_hours_worked}")
            
            assignment.save()
            print(f"Assignment saved successfully")
            
            serializer = self.get_serializer(assignment)
            return Response(serializer.data)
        except Exception as e:
            print(f"Error in clock_out: {e}")
            import traceback
            traceback.print_exc()
            raise

class AcuityBasedStaffingViewSet(FacilityAccessMixin, viewsets.ModelViewSet):
    queryset = AcuityBasedStaffing.objects.all()
    serializer_class = AcuityBasedStaffingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['shift__facility', 'shift__date']
    search_fields = ['shift__facility__name', 'shift__shift_template__name']
    ordering_fields = ['shift__date', 'recommended_staff_count']
    ordering = ['-shift__date']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter acuity staffing by facility and check access permissions"""
        queryset = AcuityBasedStaffing.objects.all()
        facility_id = self.request.query_params.get('facility')
        
        if facility_id:
            # Check if user has access to this facility
            if not self.check_facility_access(facility_id):
                return queryset.none()  # Return empty queryset if no access
            queryset = queryset.filter(shift__facility_id=facility_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            from .serializers import AcuityBasedStaffingCreateSerializer
            return AcuityBasedStaffingCreateSerializer
        return AcuityBasedStaffingSerializer

class StaffAvailabilityViewSet(FacilityAccessMixin, viewsets.ModelViewSet):
    queryset = StaffAvailability.objects.all()
    serializer_class = StaffAvailabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['availability_status', 'is_available', 'date', 'staff__role']
    search_fields = ['staff__first_name', 'staff__last_name', 'notes']
    ordering_fields = ['date', 'staff__last_name', 'availability_status']
    ordering = ['date', 'staff__last_name']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter availability by facility and check access permissions"""
        queryset = StaffAvailability.objects.all()
        facility_id = self.request.query_params.get('facility')
        
        if facility_id:
            # Check if user has access to this facility
            if not self.check_facility_access(facility_id):
                return queryset.none()  # Return empty queryset if no access
            queryset = queryset.filter(staff__facility_id=facility_id)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StaffAvailabilityCreateSerializer
        return StaffAvailabilitySerializer
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update availability for multiple staff members"""
        facility_id = request.query_params.get('facility')
        if not facility_id or not self.check_facility_access(facility_id):
            return Response(
                {'error': 'Facility access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        updates = request.data.get('updates', [])
        if not updates:
            return Response(
                {'error': 'No updates provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_count = 0
        errors = []
        
        for update in updates:
            try:
                availability_id = update.get('id')
                if availability_id:
                    # Update existing availability
                    availability = StaffAvailability.objects.get(
                        id=availability_id,
                        staff__facility_id=facility_id
                    )
                    serializer = StaffAvailabilityCreateSerializer(
                        availability, 
                        data=update, 
                        partial=True
                    )
                else:
                    # Create new availability
                    serializer = StaffAvailabilityCreateSerializer(data=update)
                
                if serializer.is_valid():
                    serializer.save()
                    updated_count += 1
                else:
                    errors.append({
                        'id': availability_id,
                        'errors': serializer.errors
                    })
            except StaffAvailability.DoesNotExist:
                errors.append({
                    'id': availability_id,
                    'errors': 'Availability record not found'
                })
            except Exception as e:
                errors.append({
                    'id': availability_id,
                    'errors': str(e)
                })
        
        return Response({
            'updated_count': updated_count,
            'errors': errors
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def weekly_summary(self, request):
        """Get weekly availability summary for a facility"""
        facility_id = request.query_params.get('facility')
        if not facility_id or not self.check_facility_access(facility_id):
            return Response(
                {'error': 'Facility access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get availability for the date range
        availability = self.get_queryset().filter(
            date__range=[start_date, end_date]
        ).select_related('staff')
        
        # Group by date and count availability statuses
        summary = {}
        for record in availability:
            date_str = record.date.isoformat()
            if date_str not in summary:
                summary[date_str] = {
                    'date': date_str,
                    'total_staff': 0,
                    'available': 0,
                    'unavailable': 0,
                    'preferred': 0,
                    'limited': 0,
                    'overtime_ok': 0,
                    'no_overtime': 0
                }
            
            summary[date_str]['total_staff'] += 1
            status = record.availability_status
            if status in summary[date_str]:
                summary[date_str][status] += 1
        
        return Response(list(summary.values()))
