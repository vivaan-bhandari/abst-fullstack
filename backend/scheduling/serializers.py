from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Staff, ShiftTemplate, Shift, StaffAssignment, 
    AcuityBasedStaffing, StaffAvailability
)
from residents.serializers import FacilitySerializer, FacilitySectionSerializer
from users.serializers import UserSerializer
import datetime
from django.utils import timezone

class StaffCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff members with user accounts"""
    username = serializers.CharField(write_only=True, required=False)  # Not required for updates
    email = serializers.EmailField(write_only=True, required=False)   # Not required for updates
    password = serializers.CharField(write_only=True, default='temp123456', required=False)  # Not required for updates
    first_name = serializers.CharField(write_only=True, required=False)  # Not required for updates
    last_name = serializers.CharField(write_only=True, required=False)   # Not required for updates
    
    class Meta:
        model = Staff
        fields = [
            'username', 'email', 'password', 'first_name', 'last_name',
            'employee_id', 'role', 'status', 'hire_date', 'facility',
            'certifications', 'skills', 'max_hours_per_week', 'preferred_shifts', 'notes'
        ]
    
    def validate_username(self, value):
        """Check if username already exists"""
        # For updates, exclude the current user from the check
        if self.instance and self.instance.user:
            if User.objects.filter(username=value).exclude(id=self.instance.user.id).exists():
                raise serializers.ValidationError("A user with this username already exists.")
        else:
            # For creation, check if any user has this username
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        """Check if email already exists"""
        # For updates, exclude the current user from the check
        if self.instance and self.instance.user:
            if User.objects.filter(email=value).exclude(id=self.instance.user.id).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        else:
            # For creation, check if any user has this email
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_employee_id(self, value):
        """Check if employee_id already exists"""
        # For updates, exclude the current staff member from the check
        if self.instance:
            if Staff.objects.filter(employee_id=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A staff member with this employee ID already exists.")
        else:
            # For creation, check if any staff member has this employee ID
            if Staff.objects.filter(employee_id=value).exists():
                raise serializers.ValidationError("A staff member with this employee ID already exists.")
        return value
    
    def create(self, validated_data):
        # Extract user data (these fields are required for creation)
        user_data = {}
        for field in ['username', 'email', 'password', 'first_name', 'last_name']:
            if field in validated_data:
                user_data[field] = validated_data.pop(field)
        
        # Validate required fields for creation
        if not all(field in user_data for field in ['username', 'email', 'password', 'first_name', 'last_name']):
            raise serializers.ValidationError("Username, email, password, first_name, and last_name are required for creating staff members.")
        
        # Create user first
        user = User.objects.create_user(**user_data)
        
        # Create staff profile linked to the user
        # Also save first_name and last_name to Staff model
        validated_data['user'] = user
        validated_data['first_name'] = user_data['first_name']
        validated_data['last_name'] = user_data['last_name']
        staff = Staff.objects.create(**validated_data)
        
        return staff
    
    def update(self, instance, validated_data):
        """Update staff member and linked user"""
        # Handle user fields if they're being updated
        user_data = {}
        if 'first_name' in validated_data:
            user_data['first_name'] = validated_data.pop('first_name')
            instance.first_name = user_data['first_name']
        if 'last_name' in validated_data:
            user_data['last_name'] = validated_data.pop('last_name')
            instance.last_name = user_data['last_name']
        if 'email' in validated_data:
            user_data['email'] = validated_data.pop('email')
        
        # Update user if there are user fields to update
        if user_data:
            user = instance.user
            for field, value in user_data.items():
                setattr(user, field, value)
            user.save()
        
        # Update staff fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    facility = FacilitySerializer(read_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'id', 'user', 'employee_id', 'first_name', 'last_name', 'full_name',
            'role', 'status', 'hire_date', 'facility', 'certifications', 'skills',
            'max_hours_per_week', 'preferred_shifts', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ShiftTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating shift templates"""
    
    class Meta:
        model = ShiftTemplate
        fields = [
            'name', 'shift_type', 'start_time', 'end_time',
            'duration_hours', 'required_staff_count',
            'required_roles', 'is_active'
        ]
        extra_kwargs = {
            'shift_type': {'required': False},  # Make it optional
            'required_roles': {'required': False}  # Make it optional
        }
    
    def create(self, validated_data):
        # Set default values if not provided
        if 'shift_type' not in validated_data:
            # Determine shift type based on time
            start_hour = validated_data['start_time'].hour
            if 6 <= start_hour < 14:
                validated_data['shift_type'] = 'day'
            elif 14 <= start_hour < 22:
                validated_data['shift_type'] = 'evening'
            else:
                validated_data['shift_type'] = 'night'
        
        if 'required_roles' not in validated_data:
            validated_data['required_roles'] = []
        
        return super().create(validated_data)

class ShiftTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftTemplate
        fields = '__all__'
        extra_kwargs = {
            'facility': {'required': False}  # Make facility optional for updates
        }

    def validate(self, data):
        # Ensure start_time and end_time are present for duration calculation
        start_time = data.get('start_time', self.instance.start_time if self.instance else None)
        end_time = data.get('end_time', self.instance.end_time if self.instance else None)

        if start_time and end_time:
            # Calculate duration if not provided or if times changed
            if 'duration_hours' not in data or \
               (self.instance and (start_time != self.instance.start_time or end_time != self.instance.end_time)):
                # Convert time objects to datetime objects for calculation (using a dummy date)
                dummy_date = datetime.date(2000, 1, 1)
                dt_start = datetime.datetime.combine(dummy_date, start_time)
                dt_end = datetime.datetime.combine(dummy_date, end_time)

                # Handle overnight shifts
                if dt_end < dt_start:
                    dt_end += datetime.timedelta(days=1)

                duration = dt_end - dt_start
                data['duration_hours'] = duration.total_seconds() / 3600

        # Infer shift_type if not provided (for both create and update)
        if 'shift_type' not in data or not data['shift_type']:
            if start_time:
                start_hour = start_time.hour
                if 6 <= start_hour < 14:
                    data['shift_type'] = 'day'
                elif 14 <= start_hour < 22:
                    data['shift_type'] = 'swing'
                else:
                    data['shift_type'] = 'noc'
            else:
                # If no start_time and no shift_type, raise an error or set a default
                # For now, let's assume start_time will always be present or inferred
                pass # Or raise serializers.ValidationError("Shift type or start time is required.")

        return data

class ShiftCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating shifts"""
    
    class Meta:
        model = Shift
        fields = [
            'date', 'shift_template', 'section', 'notes'
        ]
    
    def validate(self, data):
        # Ensure shift_template is provided
        if not data.get('shift_template'):
            raise serializers.ValidationError("Shift template is required to create a shift.")
        
        return data
    
    def create(self, validated_data):
        # Ensure the shift is created with the correct facility from the template
        shift = super().create(validated_data)
        return shift

class AcuityBasedStaffingSerializer(serializers.ModelSerializer):
    # Remove circular dependency - just use shift ID instead of full ShiftSerializer
    shift_id = serializers.IntegerField(source='shift.id', read_only=True)
    
    class Meta:
        model = AcuityBasedStaffing
        fields = [
            'id', 'shift_id', 'total_care_hours_needed', 'high_acuity_residents',
            'medium_acuity_residents', 'low_acuity_residents',
            'recommended_staff_count', 'recommended_skill_mix',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ShiftSerializer(serializers.ModelSerializer):
    shift_template = ShiftTemplateSerializer(read_only=True)
    facility = FacilitySerializer(read_only=True)
    section = FacilitySectionSerializer(read_only=True)
    is_understaffed = serializers.ReadOnlyField()
    is_overstaffed = serializers.ReadOnlyField()
    acuity_staffing = AcuityBasedStaffingSerializer(many=True, read_only=True)
    effective_staff_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Shift
        fields = [
            'id', 'date', 'shift_template', 'facility', 'section',
            'status', 'actual_start_time', 'actual_end_time', 'notes',
            'is_understaffed', 'is_overstaffed', 'acuity_staffing', 'effective_staff_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_understaffed', 'is_overstaffed']
    
    def get_effective_staff_count(self, obj):
        """Get the effective staff count, prioritizing acuity-based staffing over template default"""
        # Check if there's an acuity-based staffing record
        acuity_staffing = obj.acuity_staffing.first()
        if acuity_staffing and acuity_staffing.recommended_staff_count:
            return acuity_staffing.recommended_staff_count
        
        # Fall back to shift template's required staff count
        return obj.shift_template.required_staff_count if obj.shift_template else 1

class StaffAssignmentSerializer(serializers.ModelSerializer):
    staff = StaffSerializer(read_only=True)
    shift = ShiftSerializer(read_only=True)
    
    class Meta:
        model = StaffAssignment
        fields = [
            'id', 'staff', 'shift', 'assigned_role', 'clock_in_time',
            'clock_out_time', 'actual_hours_worked', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class StaffAssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff assignments"""
    
    class Meta:
        model = StaffAssignment
        fields = [
            'staff', 'shift', 'assigned_role', 'clock_in_time',
            'clock_out_time', 'actual_hours_worked', 'notes'
        ]
    
    def validate(self, data):
        # Ensure staff is provided
        if not data.get('staff'):
            raise serializers.ValidationError("Staff member is required.")
        
        # Ensure shift is provided
        if not data.get('shift'):
            raise serializers.ValidationError("Shift is required.")
        
        # Ensure assigned_role is provided
        if not data.get('assigned_role'):
            raise serializers.ValidationError("Assigned role is required.")
        
        # Ensure staff and shift belong to the same facility
        staff = data.get('staff')
        shift = data.get('shift')
        
        if staff and shift:
            # Get staff facility
            if hasattr(staff, 'facility'):
                staff_facility = staff.facility
            else:
                try:
                    from .models import Staff
                    staff_obj = Staff.objects.get(id=staff)
                    staff_facility = staff_obj.facility
                except Staff.DoesNotExist:
                    raise serializers.ValidationError("Invalid staff member.")
            
            # Get shift facility
            if hasattr(shift, 'facility'):
                shift_facility = shift.facility
            else:
                try:
                    from .models import Shift
                    shift_obj = Shift.objects.get(id=shift)
                    shift_facility = shift_obj.facility
                except Shift.DoesNotExist:
                    raise serializers.ValidationError("Invalid shift.")
            
            if staff_facility.id != shift_facility.id:
                raise serializers.ValidationError("Staff member and shift must belong to the same facility.")
        
        return data
    
    def create(self, validated_data):
        # Set default values for required fields
        if 'actual_hours_worked' not in validated_data:
            # Get the shift template to calculate default hours
            shift_id = validated_data['shift']
            try:
                from .models import Shift
                shift = Shift.objects.get(id=shift_id)
                
                # Handle both object and ID for shift_template
                template = shift.shift_template
                if hasattr(template, 'duration_hours') and template.duration_hours:
                    validated_data['actual_hours_worked'] = template.duration_hours
                else:
                    validated_data['actual_hours_worked'] = 8.0
            except Shift.DoesNotExist:
                validated_data['actual_hours_worked'] = 8.0
            except Exception as e:
                print(f"Error in StaffAssignmentCreateSerializer.create: {e}")
                validated_data['actual_hours_worked'] = 8.0
        
        return super().create(validated_data)

class AcuityBasedStaffingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating acuity staffing records"""
    
    class Meta:
        model = AcuityBasedStaffing
        fields = [
            'shift', 'total_care_hours_needed', 'high_acuity_residents',
            'medium_acuity_residents', 'low_acuity_residents',
            'recommended_staff_count', 'recommended_skill_mix'
        ]
    
    def validate(self, data):
        # Ensure shift belongs to the same facility as the user
        shift = data.get('shift')
        if shift:
            # This validation will be handled by the view's facility access check
            pass
        
        # Validate that recommended_staff_count is positive
        staff_count = data.get('recommended_staff_count')
        if staff_count and staff_count <= 0:
            raise serializers.ValidationError("Recommended staff count must be positive.")
        
        # Validate that care hours are positive
        care_hours = data.get('total_care_hours_needed')
        if care_hours and care_hours <= 0:
            raise serializers.ValidationError("Total care hours must be positive.")
        
        return data

class StaffAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for staff availability"""
    staff_name = serializers.CharField(source='staff.full_name', read_only=True)
    staff_role = serializers.CharField(source='staff.role', read_only=True)
    facility_name = serializers.CharField(source='staff.facility.name', read_only=True)
    
    class Meta:
        model = StaffAvailability
        fields = [
            'id', 'staff', 'staff_name', 'staff_role', 'facility_name',
            'date', 'availability_status', 'is_available',
            'preferred_start_time', 'preferred_end_time', 'max_hours',
            'preferred_shifts', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class StaffAvailabilityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff availability"""
    
    class Meta:
        model = StaffAvailability
        fields = [
            'staff', 'date', 'availability_status', 'preferred_start_time',
            'preferred_end_time', 'max_hours', 'preferred_shifts', 'notes'
        ]
    
    def validate(self, data):
        # Ensure staff belongs to the same facility as the user
        staff = data.get('staff')
        if staff:
            # This validation will be handled by the view's facility access check
            pass
        
        # Validate date is not in the past
        date = data.get('date')
        if date and date < timezone.now().date():
            raise serializers.ValidationError("Cannot set availability for past dates.")
        
        # Validate time ranges if both are provided
        start_time = data.get('preferred_start_time')
        end_time = data.get('preferred_end_time')
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError("Preferred start time must be before end time.")
        
        return data

# Nested serializers for detailed views
class ShiftDetailSerializer(ShiftSerializer):
    staff_assignments = StaffAssignmentSerializer(many=True, read_only=True)
    acuity_staffing = AcuityBasedStaffingSerializer(many=True, read_only=True)
    
    class Meta(ShiftSerializer.Meta):
        fields = ShiftSerializer.Meta.fields + ['staff_assignments', 'acuity_staffing']

class StaffDetailSerializer(StaffSerializer):
    assignments = StaffAssignmentSerializer(many=True, read_only=True)
    availability = StaffAvailabilitySerializer(many=True, read_only=True)
    
    class Meta(StaffSerializer.Meta):
        fields = StaffSerializer.Meta.fields + ['assignments', 'availability']
