from rest_framework import serializers
from .models import Staff, ShiftTemplate, Shift, StaffAssignment, StaffAvailability, AIInsight, AIRecommendation
from residents.serializers import FacilitySerializer


class StaffSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.IntegerField(write_only=True)
    full_name = serializers.ReadOnlyField()
    hire_date = serializers.DateField(input_formats=['%Y-%m-%d', '%m/%d/%Y'], format='%Y-%m-%d')
    
    class Meta:
        model = Staff
        fields = [
            'id', 'first_name', 'last_name', 'email', 'employee_id', 'role',
            'hire_date', 'status', 'max_hours', 'notes', 'facility', 'facility_id',
            'created_at', 'updated_at', 'full_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_email(self, value):
        # Check if email is unique across all facilities
        if Staff.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("A staff member with this email already exists.")
        return value
    
    def validate_employee_id(self, value):
        # Check if employee ID is unique across all facilities
        if Staff.objects.filter(employee_id=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("A staff member with this employee ID already exists.")
        return value
    
    def validate_hire_date(self, value):
        # Ensure the date is properly formatted
        if value:
            print(f"DEBUG: Received hire_date value: {value} (type: {type(value)})")
            # Convert to string and back to ensure proper formatting
            if isinstance(value, str):
                from datetime import datetime
                try:
                    # Try parsing with different formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y']:
                        try:
                            parsed_date = datetime.strptime(value, fmt)
                            print(f"DEBUG: Successfully parsed date with format {fmt}: {parsed_date.date()}")
                            return parsed_date.date()
                        except ValueError:
                            print(f"DEBUG: Failed to parse with format {fmt}")
                            continue
                    print(f"DEBUG: All parsing attempts failed for value: {value}")
                    raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY.")
                except Exception as e:
                    print(f"DEBUG: Exception during parsing: {e}")
                    raise serializers.ValidationError("Invalid date format. Use YYYY-MM-DD or MM/DD/YYYY.")
            return value
        return value


class ShiftTemplateSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.IntegerField(write_only=True)
    start_time = serializers.TimeField(input_formats=['%H:%M', '%H:%M:%S'])
    end_time = serializers.TimeField(input_formats=['%H:%M', '%H:%M:%S'])
    
    class Meta:
        model = ShiftTemplate
        fields = [
            'id', 'template_name', 'shift_type', 'start_time', 'end_time',
            'duration', 'required_staff', 'is_active', 'facility', 'facility_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        print(f"🔍 ShiftTemplate validation data: {data}")
        print(f"🔍 Time fields - start: {data.get('start_time')} (type: {type(data.get('start_time'))})")
        print(f"🔍 Time fields - end: {data.get('end_time')} (type: {type(data.get('end_time'))})")
        
        # Validate that end time is after start time
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time.")
        
        # Validate duration matches time difference
        start_minutes = data['start_time'].hour * 60 + data['start_time'].minute
        end_minutes = data['end_time'].hour * 60 + data['end_time'].minute
        
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60  # Add 24 hours for overnight shifts
        
        calculated_duration = (end_minutes - start_minutes) / 60
        if abs(calculated_duration - float(data['duration'])) > 0.1:
            raise serializers.ValidationError("Duration must match the time difference between start and end times.")
        
        return data


class ShiftSerializer(serializers.ModelSerializer):
    shift_template = ShiftTemplateSerializer(read_only=True)
    shift_template_id = serializers.IntegerField(write_only=True)
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.IntegerField(write_only=True)
    date = serializers.DateField(input_formats=['%Y-%m-%d', '%m/%d/%Y'], format='%Y-%m-%d')
    
    # Properties from shift template
    shift_type = serializers.ReadOnlyField()
    start_time = serializers.ReadOnlyField()
    end_time = serializers.ReadOnlyField()
    duration = serializers.ReadOnlyField()
    
    class Meta:
        model = Shift
        fields = [
            'id', 'date', 'shift_template', 'shift_template_id', 'facility', 'facility_id',
            'required_staff_count', 'required_staff_role', 'shift_type', 'start_time',
            'end_time', 'duration', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StaffAssignmentSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    staff_id = serializers.IntegerField(write_only=True)
    shift = ShiftSerializer(read_only=True)
    shift_id = serializers.IntegerField(write_only=True)
    assigned_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    confirmed_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)
    
    class Meta:
        model = StaffAssignment
        fields = [
            'id', 'staff', 'staff_id', 'shift', 'shift_id', 'status',
            'assigned_at', 'confirmed_at', 'notes'
        ]
        read_only_fields = ['id', 'assigned_at']


class StaffAvailabilitySerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    staff_id = serializers.IntegerField(write_only=True)
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.IntegerField(write_only=True)
    date = serializers.DateField(input_formats=['%Y-%m-%d', '%m/%d/%Y'], format='%Y-%m-%d')
    preferred_start_time = serializers.TimeField(required=False, allow_null=True, input_formats=['%H:%M', '%H:%M:%S'])
    preferred_end_time = serializers.TimeField(required=False, allow_null=True, input_formats=['%H:%M', '%H:%M:%S'])
    preferred_shift_types = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    
    class Meta:
        model = StaffAvailability
        fields = [
            'id', 'staff', 'staff_id', 'date', 'availability_status', 'max_hours',
            'preferred_start_time', 'preferred_end_time', 'preferred_shift_types',
            'notes', 'facility', 'facility_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Convert empty strings to None for time fields
        if data.get('preferred_start_time') == '':
            data['preferred_start_time'] = None
        if data.get('preferred_end_time') == '':
            data['preferred_end_time'] = None
            
        print(f"DEBUG: StaffAvailability validation data: {data}")
        print(f"DEBUG: Time fields - start: {data.get('preferred_start_time')} (type: {type(data.get('preferred_start_time'))})")
        print(f"DEBUG: Time fields - end: {data.get('preferred_end_time')} (type: {type(data.get('preferred_end_time'))})")
        print(f"DEBUG: All field types: {[(k, type(v)) for k, v in data.items()]}")
        
        # Check if this is an update or create
        if self.instance:
            print(f"DEBUG: This is an UPDATE for instance {self.instance.id}")
        else:
            print("DEBUG: This is a CREATE operation")
        
        # Check for duplicate availability (only for new records, not updates)
        if 'staff_id' in data and 'date' in data and 'facility_id' in data:
            from scheduling.models import StaffAvailability
            
            # Get the current instance if this is an update
            current_instance = self.instance
            
            try:
                existing = StaffAvailability.objects.filter(
                    staff_id=data['staff_id'],
                    date=data['date'],
                    facility_id=data['facility_id']
                ).exclude(id=current_instance.id if current_instance else None).first()
                
                if existing:
                    raise serializers.ValidationError(
                        f"Staff availability already exists for this staff member on {data['date']}. "
                        "Please update the existing record or choose a different date."
                    )
            except Exception as e:
                print(f"DEBUG: Error during duplicate check: {e}")
                # Don't fail validation on database errors, just log them
                pass
        
        # Validate preferred times if both are provided
        if data.get('preferred_start_time') and data.get('preferred_end_time'):
            start_time = data['preferred_start_time']
            end_time = data['preferred_end_time']
            
            print(f"DEBUG: Start time: {start_time} (type: {type(start_time)})")
            print(f"DEBUG: End time: {end_time} (type: {type(end_time)})")
            
            try:
                # Check if end time is after start time
                if end_time <= start_time:
                    raise serializers.ValidationError("Preferred end time must be after preferred start time.")
                
                # Calculate duration in hours
                from datetime import datetime, timedelta
                start_dt = datetime.combine(datetime.today(), start_time)
                end_dt = datetime.combine(datetime.today(), end_time)
                
                # Handle overnight shifts
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)
                
                duration_hours = (end_dt - start_dt).total_seconds() / 3600
                print(f"DEBUG: Calculated duration: {duration_hours} hours")
                
                # Allow shorter time ranges but provide guidance
                if duration_hours < 0.5:  # Less than 30 minutes
                    raise serializers.ValidationError("Preferred time range is too short (less than 30 minutes). Please specify a meaningful time window.")
                elif duration_hours < 1.0:  # Less than 1 hour
                    # This might be intentional for specific time preferences
                    print(f"DEBUG: Short time range detected: {duration_hours} hours - this might be intentional")
            except Exception as e:
                print(f"DEBUG: Error during time validation: {e}")
                # If there's an error with time validation, just log it and continue
                # This prevents crashes from malformed time data
                pass
        
        return data


class AIInsightSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.IntegerField(write_only=True)
    date = serializers.DateField(input_formats=['%Y-%m-%d', '%m/%d/%Y'], format='%Y-%m-%d')
    
    class Meta:
        model = AIInsight
        fields = [
            'id', 'facility', 'facility_id', 'date', 'total_residents',
            'total_care_hours', 'avg_acuity_score', 'staffing_efficiency',
            'low_acuity_count', 'medium_acuity_count', 'high_acuity_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AIRecommendationSerializer(serializers.ModelSerializer):
    facility = FacilitySerializer(read_only=True)
    facility_id = serializers.IntegerField(write_only=True)
    date = serializers.DateField(input_formats=['%Y-%m-%d', '%m/%d/%Y'], format='%Y-%m-%d')
    
    class Meta:
        model = AIRecommendation
        fields = [
            'id', 'facility', 'facility_id', 'date', 'shift_type', 'care_hours',
            'required_staff', 'resident_count', 'confidence', 'applied', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Summary serializers for dashboard stats
class StaffSummarySerializer(serializers.Serializer):
    count = serializers.IntegerField()
    active_count = serializers.IntegerField()
    inactive_count = serializers.IntegerField()


class ShiftSummarySerializer(serializers.Serializer):
    count = serializers.IntegerField()
    day_count = serializers.IntegerField()
    swing_count = serializers.IntegerField()
    noc_count = serializers.IntegerField()


class AssignmentSummarySerializer(serializers.Serializer):
    count = serializers.IntegerField()
    confirmed_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()


class DashboardStatsSerializer(serializers.Serializer):
    total_staff = serializers.IntegerField()
    total_shifts = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    understaffed_shifts = serializers.IntegerField()
    staffing_efficiency = serializers.DecimalField(max_digits=5, decimal_places=2)
