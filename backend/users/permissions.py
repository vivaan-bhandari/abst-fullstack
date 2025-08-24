from rest_framework import permissions
from .models import FacilityAccess

class HasFacilityAccess(permissions.BasePermission):
    """
    Custom permission to check if user has access to a specific facility.
    """
    
    def has_permission(self, request, view):
        # Allow admins to access everything
        if request.user.is_staff or getattr(request.user, 'role', None) == 'admin':
            return True
        
        # For facility-specific data, check if user has access
        facility_id = request.data.get('facility_id') or request.data.get('facility') or request.query_params.get('facility')
        if facility_id:
            return FacilityAccess.objects.filter(
                user=request.user,
                facility_id=facility_id,
                status='approved'
            ).exists()
        
        return True
    
    def has_object_permission(self, request, view, obj):
        # Allow admins to access everything
        if request.user.is_staff or getattr(request.user, 'role', None) == 'admin':
            return True
        
        # For facility-specific data, check if user has access to the object's facility
        if hasattr(obj, 'facility'):
            return FacilityAccess.objects.filter(
                user=request.user,
                facility=obj.facility,
                status='approved'
            ).exists()
        
        return True

class IsFacilityAdmin(permissions.BasePermission):
    """
    Custom permission to check if user is a facility admin.
    """
    
    def has_permission(self, request, view):
        # Allow system admins
        if request.user.is_staff or getattr(request.user, 'role', None) == 'admin':
            return True
        
        # Check if user is a facility admin for the specific facility
        facility_id = request.data.get('facility_id') or request.data.get('facility') or request.query_params.get('facility')
        if facility_id:
            return FacilityAccess.objects.filter(
                user=request.user,
                facility_id=facility_id,
                role='facility_admin',
                status='approved'
            ).exists()
        
        return False

class CanManageUsers(permissions.BasePermission):
    """
    Custom permission to check if user can manage other users.
    """
    
    def has_permission(self, request, view):
        # Allow system admins
        if request.user.is_staff or getattr(request.user, 'role', None) == 'admin':
            return True
        
        # Allow facility admins for user management within their facility
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False 