from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import ADL, ADLQuestion
from .serializers import ADLSerializer, ADLQuestionSerializer
from residents.models import Resident
from residents.serializers import ResidentSerializer
import pandas as pd
import io


class ADLViewSet(viewsets.ModelViewSet):
    queryset = ADL.objects.filter(is_deleted=False)
    serializer_class = ADLSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['resident', 'status', 'question_text']
    search_fields = ['question_text', 'resident__name', 'status']
    ordering_fields = ['created_at', 'total_minutes', 'total_hours', 'resident__name']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        
        # Superadmins and admins see all ADLs
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            return ADL.objects.filter(is_deleted=False)

        # Get approved facility IDs for this user
        from users.models import FacilityAccess
        from residents.models import FacilitySection, Resident
        approved_facility_ids = FacilityAccess.objects.filter(
            user=user,
            status='approved'
        ).values_list('facility_id', flat=True)
        
        # Get all sections in those facilities
        allowed_sections = FacilitySection.objects.filter(facility_id__in=approved_facility_ids)
        
        # Get all residents in those sections
        allowed_residents = Resident.objects.filter(facility_section__in=allowed_sections)
        
        # Only ADLs for allowed residents
        return ADL.objects.filter(resident__in=allowed_residents, is_deleted=False)

    def perform_update(self, serializer):
        """Custom update to validate and save ADL"""
        instance = serializer.instance
        data = serializer.validated_data
        
        # Calculate total_minutes and total_hours
        minutes = data.get('minutes', instance.minutes)
        frequency = data.get('frequency', instance.frequency)
        per_day_shift_times = data.get('per_day_shift_times', getattr(instance, 'per_day_shift_times', {}))
        
        # Sum all per-day/shift times
        per_day_shift_total = 0
        if per_day_shift_times:
            per_day_shift_total = sum(int(v) for v in per_day_shift_times.values() if v)
        
        if per_day_shift_total > 0:
            total_minutes = per_day_shift_total
        else:
            total_minutes = minutes * frequency
        total_hours = float(total_minutes) / 60 if total_minutes else 0
        
        # Update the calculated fields and ensure per_day_shift_times is saved
        serializer.save(
            total_minutes=total_minutes,
            total_hours=total_hours,
            per_day_shift_times=per_day_shift_times,
            updated_by=self.request.user,
            updated_at=timezone.now()
        )

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete"""
        instance.soft_delete()

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a soft-deleted ADL"""
        instance = self.get_object()
        instance.restore()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def deleted(self, request):
        """View soft-deleted ADLs"""
        queryset = ADL.objects.filter(is_deleted=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_resident(self, request):
        """Get all ADLs grouped by resident"""
        resident_id = request.query_params.get('resident_id')
        if resident_id:
            adls = self.queryset.filter(resident_id=resident_id)
        else:
            adls = self.queryset.all()
        
        serializer = self.get_serializer(adls, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Get ADLs grouped by date"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        adls = self.queryset.all()
        if start_date:
            adls = adls.filter(created_at__date__gte=start_date)
        if end_date:
            adls = adls.filter(created_at__date__lte=end_date)
            
        adls = adls.annotate(date=TruncDate('created_at')).order_by('-date')
        serializer = self.get_serializer(adls, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics of ADLs, with optional resident or facility filtering"""
        resident_id = request.query_params.get('resident_id')
        facility_id = request.query_params.get('facility_id')
        queryset = self.queryset
        if resident_id:
            queryset = queryset.filter(resident_id=resident_id)
        if facility_id:
            # Filter by residents in the given facility
            from residents.models import Resident, FacilitySection
            sections = FacilitySection.objects.filter(facility_id=facility_id)
            residents = Resident.objects.filter(facility_section__in=sections)
            queryset = queryset.filter(resident__in=residents)
        summary = queryset.aggregate(
            total_minutes=Sum('total_minutes'),
            total_hours=Sum('total_hours'),
            avg_minutes_per_task=Avg('minutes'),
            total_adls=Count('id')
        )
        return Response(summary)

    @action(detail=False, methods=['get'])
    def by_facility(self, request):
        """Get all ADLs for a facility"""
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            return Response({'error': 'facility_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get all residents in the facility
        from residents.models import Resident, FacilitySection
        sections = FacilitySection.objects.filter(facility_id=facility_id)
        residents = Resident.objects.filter(facility_section__in=sections)
        
        # Get all ADLs for those residents
        adls = self.get_queryset().filter(resident__in=residents)
        
        serializer = self.get_serializer(adls, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='questions', permission_classes=[AllowAny])
    def list_questions(self, request):
        """Return the full list of ADLQuestions, ordered."""
        questions = ADLQuestion.objects.all().order_by('order', 'id')
        serializer = ADLQuestionSerializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='seed', permission_classes=[AllowAny])
    def seed_questions(self, request):
        """Manually seed ADL questions"""
        from .seed_adl_questions import seed_adl_questions
        try:
            seed_adl_questions()
            questions = ADLQuestion.objects.all().order_by('order', 'id')
            serializer = ADLQuestionSerializer(questions, many=True)
            return Response({
                'message': f'Successfully seeded {questions.count()} ADL questions',
                'questions': serializer.data
            })
        except Exception as e:
            return Response({
                'error': f'Failed to seed questions: {str(e)}'
            }, status=500)

    def perform_create(self, serializer):
        data = serializer.validated_data
        minutes = data.get('minutes', 0)
        frequency = data.get('frequency', 0)
        per_day_shift_times = data.get('per_day_shift_times', {})
        per_day_shift_total = sum(int(v) for v in per_day_shift_times.values() if v)
        if per_day_shift_total > 0:
            total_minutes = per_day_shift_total
        else:
            total_minutes = minutes * frequency
        total_hours = float(total_minutes) / 60 if total_minutes else 0
        serializer.save(
            total_minutes=total_minutes,
            total_hours=total_hours,
            created_by=self.request.user,
            updated_by=self.request.user
        )

    @action(detail=False, methods=['get'])
    def caregiving_summary(self, request):
        from residents.models import Resident, FacilitySection, Facility
        from .models import ADL
        from users.models import FacilityAccess
        
        # Use the same filtering logic as get_queryset
        user = request.user
        
        print(f"DEBUG: User: {user.username}, is_staff: {user.is_staff}, role: {getattr(user, 'role', None)}")
        
        # Initialize variables
        adls = None
        residents = None
        
        # Superadmins and admins see all ADLs
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            print("DEBUG: User is staff/admin - checking if facility filter is applied")
            # Check if a specific facility is requested
            facility_id = request.query_params.get('facility_id')
            if facility_id:
                # Specific facility selected - filter by that facility only
                print(f"DEBUG: Staff/admin user selected specific facility: {facility_id}")
                sections = FacilitySection.objects.filter(facility_id=facility_id)
                residents = Resident.objects.filter(facility_section__in=sections)
                adls = ADL.objects.filter(resident__in=residents, is_deleted=False)
                print(f"DEBUG: Filtered to {residents.count()} residents in facility {facility_id}")
            else:
                # No facility selected - show ALL ADLs (aggregated view)
                print("DEBUG: Staff/admin user - no facility selected, showing ALL ADLs for aggregation")
                adls = ADL.objects.filter(is_deleted=False)
        else:
            print("DEBUG: User is NOT staff/admin - applying facility access filtering")
            # For anonymous users, return empty data
            if user.is_anonymous:
                return Response({
                    'per_shift': [{'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']],
                    'per_day': [{'day': day, 'hours': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                })
            
            # For aggregated view (no facility selected), show ALL ADL
            # For specific facility view, filter by that facility only
            facility_id = request.query_params.get('facility_id')
            
            if facility_id:
                # Specific facility selected - filter by that facility only
                print(f"DEBUG: Specific facility selected: {facility_id}")
                approved_facility_ids = FacilityAccess.objects.filter(
                    user=user,
                    status='approved'
                ).values_list('facility_id', flat=True)
                
                if int(facility_id) not in approved_facility_ids:
                    return Response({'error': 'Access denied to this facility'}, status=403)
                
                # Get sections and residents for this specific facility
                sections = FacilitySection.objects.filter(facility_id=facility_id)
                residents = Resident.objects.filter(facility_section__in=sections)
                adls = ADL.objects.filter(resident__in=residents, is_deleted=False)
                print(f"DEBUG: Filtered to {residents.count()} residents in facility {facility_id}")
            else:
                # No facility selected - show ALL ADLs (aggregated view)
                print("DEBUG: No facility selected - showing ALL ADLs for aggregation")
                adls = ADL.objects.filter(is_deleted=False)
        
        # If residents is not defined yet (for staff/admin users), get all residents
        if residents is None:
            residents = Resident.objects.filter(adls__in=adls).distinct()
            print("DEBUG: Using all residents for staff/admin user")
        
        # Facility filtering is now handled above in the user permission logic
        
        shift_map = {
            'Shift1': 'Day',
            'Shift2': 'Swing',  # Changed from 'Eve' to 'Swing' to match frontend
            'Shift3': 'NOC',
        }
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_prefixes = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
        per_shift = [
            {'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in days  # Changed 'Eve' to 'Swing'
        ]
        
        # Calculate chart data directly from ADL records
        # Check if we have a facility_id parameter from the request
        request_facility_id = request.query_params.get('facility_id')
        if request_facility_id:
            # We already have the filtered residents for this specific facility
            print(f"DEBUG: Using pre-filtered residents for facility {request_facility_id}")
            # Don't override the residents variable - keep using the pre-filtered ones
        else:
            # No facility selected - get all residents from ADLs for aggregation
            residents = Resident.objects.filter(adls__in=adls).distinct()
            print("DEBUG: Using all residents for aggregation")
        
        # Debug: print which facilities are being processed
        facility_counts = {}
        for resident in residents:
            facility_name = resident.facility_section.facility.name
            facility_counts[facility_name] = facility_counts.get(facility_name, 0) + 1
        
        print(f"DEBUG: Request facility_id: {request_facility_id}")
        print(f"DEBUG: Facilities being processed: {facility_counts}")
        print(f"DEBUG: Total residents being processed: {residents.count()}")
        if request_facility_id:
            print(f"DEBUG: Expected: Only residents from facility {request_facility_id}")
        else:
            print(f"DEBUG: Expected: All residents from all facilities (aggregated)")
        
        total_hours_processed = 0
        total_adls_processed = 0
        
        # FIXED: Use resident total_shift_times instead of ADL records for aggregation
        # This matches how individual facility charts work
        for resident in residents:
            resident_total_times = resident.total_shift_times or {}
            if resident_total_times:
                print(f"DEBUG: Resident {resident.name} has total_shift_times: {resident_total_times}")
                # Process resident's total shift times (like Oregon ABST)
                for day_key, minutes in resident_total_times.items():
                    if minutes and minutes > 0:
                        # Parse the column name (e.g., "ResidentTotalMonShift1Time" -> Monday, Day)
                        day_name = None
                        shift_type = None
                        
                        # Parse the day
                        if 'Mon' in day_key:
                            day_name = 0  # Monday
                        elif 'Tues' in day_key:
                            day_name = 1  # Tuesday
                        elif 'Wed' in day_key:
                            day_name = 2  # Wednesday
                        elif 'Thurs' in day_key:
                            day_name = 3  # Thursday
                        elif 'Fri' in day_key:
                            day_name = 4  # Friday
                        elif 'Sat' in day_key:
                            day_name = 5  # Saturday
                        elif 'Sun' in day_key:
                            day_name = 6  # Sunday
                        
                        # Parse the shift type
                        if 'Shift1' in day_key:
                            shift_type = 'Day'
                        elif 'Shift2' in day_key:
                            shift_type = 'Swing'
                        elif 'Shift3' in day_key:
                            shift_type = 'NOC'
                        
                        if day_name is not None and shift_type is not None:
                            # Convert minutes to hours directly
                            hours = minutes / 60.0
                            per_shift[day_name][shift_type] += hours
                            total_hours_processed += hours
                            print(f"DEBUG: Added {hours:.2f} hours to {per_shift[day_name]['day']} {shift_type} (minutes: {minutes}) from resident {resident.name}")
            else:
                print(f"DEBUG: Resident {resident.name} has NO total_shift_times data")
        
        # Fallback: If no resident total_shift_times data, try ADL records
        if total_hours_processed == 0:
            print("DEBUG: No resident total_shift_times data found, falling back to ADL records...")
            for resident in residents:
                # Get all ADLs for this resident
                resident_adls = adls.filter(resident=resident)
                for adl in resident_adls:
                    total_adls_processed += 1
                    hours_added = 0
                    
                    # Use per_day_shift_times as actual minutes (not frequency)
                    if adl.per_day_shift_times and isinstance(adl.per_day_shift_times, dict):
                        # per_day_shift_times contains actual minutes for each shift
                        for day_key, minutes in adl.per_day_shift_times.items():
                            if minutes and minutes > 0:  # Only process shifts with actual minutes
                                # Parse the column name (e.g., "MonShift1Time" -> Monday, Day)
                                day_name = None
                                shift_type = None
                                
                                # Parse the day
                                if 'Mon' in day_key:
                                    day_name = 0  # Monday
                                elif 'Tues' in day_key:
                                    day_name = 1  # Tuesday
                                elif 'Wed' in day_key:
                                    day_name = 2  # Wednesday
                                elif 'Thurs' in day_key:
                                    day_name = 3  # Thursday
                                elif 'Fri' in day_key:
                                    day_name = 4  # Friday
                                elif 'Sat' in day_key:
                                    day_name = 5  # Saturday
                                elif 'Sun' in day_key:
                                    day_name = 6  # Sunday
                                
                                # Parse the shift type
                                if 'Shift1' in day_key:
                                    shift_type = 'Day'
                                elif 'Shift2' in day_key:
                                    shift_type = 'Swing'  # Changed from 'Eve' to 'Swing'
                                elif 'Shift3' in day_key:
                                    shift_type = 'NOC'
                                
                                if day_name is not None and shift_type is not None:
                                    # Convert minutes to hours directly
                                    hours = minutes / 60.0
                                    per_shift[day_name][shift_type] += hours
                                    hours_added += hours
                                    print(f"DEBUG: Added {hours:.2f} hours to {per_shift[day_name]['day']} {shift_type} (minutes: {minutes})")
                    
                    # If no per_day_shift_times or no hours were added, use total_minutes as fallback
                    if hours_added == 0 and adl.total_minutes and adl.total_minutes > 0:
                        # Distribute total_minutes evenly across all days and shifts
                        minutes_per_day = adl.total_minutes / 7.0
                        hours_per_day = minutes_per_day / 60.0
                        
                        # Distribute evenly across all three shifts
                        hours_per_shift = hours_per_day / 3.0
                        
                        for i in range(7):
                            per_shift[i]['Day'] += hours_per_shift
                            per_shift[i]['Swing'] += hours_per_shift
                            per_shift[i]['NOC'] += hours_per_shift
                        
                        total_hours_processed += adl.total_minutes / 60.0
                        print(f"DEBUG: Fallback - distributed {adl.total_minutes} minutes ({hours_per_day:.2f} hours per day, {hours_per_shift:.2f} per shift) for resident {adl.resident.name}")
                    elif hours_added > 0:
                        total_hours_processed += hours_added

        for s in per_shift:
            for shift in ['Day', 'Swing', 'NOC']:  # Changed 'Eve' to 'Swing'
                s[shift] = round(s[shift], 2)
        per_day = [
            {'day': s['day'], 'hours': round(s['Day'] + s['Swing'] + s['NOC'], 2)}  # Changed 'Eve' to 'Swing'
            for s in per_shift
        ]
        
        # Debug logging
        print(f"DEBUG: ADL count: {adls.count()}")
        print(f"DEBUG: Resident count: {residents.count()}")
        print(f"DEBUG: Total ADLs processed: {total_adls_processed}")
        print(f"DEBUG: Total hours processed: {total_hours_processed:.2f}")
        
        # Debug: Show expected totals from individual facilities
        print(f"DEBUG: Expected totals from individual facilities:")
        for facility_name, resident_count in facility_counts.items():
            facility_residents = [r for r in residents if r.facility_section.facility.name == facility_name]
            facility_total_hours = 0
            for resident in facility_residents:
                resident_total_times = resident.total_shift_times or {}
                for minutes in resident_total_times.values():
                    if minutes and minutes > 0:
                        facility_total_hours += minutes / 60.0
            print(f"  {facility_name}: {facility_total_hours:.2f} hours ({resident_count} residents)")
        
        print(f"DEBUG: Per shift data: {per_shift}")
        print(f"DEBUG: Per day data: {per_day}")
        
        # Additional debugging for first few ADLs
        sample_adls = adls[:3]
        for i, adl in enumerate(sample_adls):
            print(f"DEBUG: ADL {i+1}: resident={adl.resident.name}, total_minutes={adl.total_minutes}, per_day_shift_times={adl.per_day_shift_times}")
        
        return Response({
            'per_shift': per_shift,
            'per_day': per_day
        })
