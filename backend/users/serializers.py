from django.contrib.auth.models import User
from rest_framework import serializers
from .models import FacilityAccess
from residents.models import Facility

class FacilitySerializer(serializers.ModelSerializer):
    """Serializer for facility details"""
    class Meta:
        model = Facility
        fields = ['id', 'name', 'address', 'city', 'state', 'zip_code', 'phone', 'email', 'facility_type', 'facility_id', 'admin_name']

class FacilityAccessSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    facility = FacilitySerializer(read_only=True)  # Include full facility details
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    
    class Meta:
        model = FacilityAccess
        fields = ['id', 'user', 'facility', 'role', 'status', 'user_username', 'user_email', 'facility_name']
        read_only_fields = ['status']  # Status can only be changed by admins

class FacilityAccessRequestSerializer(serializers.ModelSerializer):
    """Serializer for users to request facility access"""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    facility = serializers.PrimaryKeyRelatedField(queryset=Facility.objects.all())
    
    class Meta:
        model = FacilityAccess
        fields = ['user', 'facility', 'role']
        read_only_fields = ['user', 'status']

class FacilityAccessAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for superadmins to assign facility access"""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    facility = serializers.PrimaryKeyRelatedField(queryset=Facility.objects.all())
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    
    class Meta:
        model = FacilityAccess
        fields = ['id', 'user', 'facility', 'role', 'status', 'user_username', 'user_email', 'facility_name']
    
    def create(self, validated_data):
        # Set status to approved for superadmin assignments
        validated_data['status'] = 'approved'
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Set status to approved for superadmin assignments
        validated_data['status'] = 'approved'
        return super().update(instance, validated_data)

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration and profile"""
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    is_staff = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'is_staff']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

class FacilityAccessApprovalSerializer(serializers.ModelSerializer):
    """Serializer for admins to approve/deny access requests"""
    class Meta:
        model = FacilityAccess
        fields = ['status'] 