from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import (
    FacilityAccessSerializer, 
    FacilityAccessRequestSerializer,
    FacilityAccessApprovalSerializer,
    FacilityAccessAssignmentSerializer,
    UserSerializer
)
from .models import FacilityAccess
from residents.models import Facility



class FacilityAccessViewSet(viewsets.ModelViewSet):
    queryset = FacilityAccess.objects.all()
    serializer_class = FacilityAccessSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def debug_access(self, request):
        """Debug endpoint to check facility access without authentication"""
        total_access = FacilityAccess.objects.count()
        approved_access = FacilityAccess.objects.filter(status='approved').count()
        
        # Get all users and their access
        users = User.objects.all()
        user_access_summary = []
        
        for user in users:
            access_records = FacilityAccess.objects.filter(user=user)
            approved_records = access_records.filter(status='approved')
            user_access_summary.append({
                'username': user.username,
                'is_staff': user.is_staff,
                'total_access': access_records.count(),
                'approved_access': approved_records.count(),
                'facilities': list(approved_records.values_list('facility__name', flat=True))
            })
        
        return Response({
            'total_access_records': total_access,
            'approved_access_records': approved_access,
            'users': user_access_summary
        })
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        
        # Superadmins and admins can see all access records
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            return FacilityAccess.objects.all()
        
        # Regular users can only see their own access records
        return FacilityAccess.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Use different serializers based on action and user role"""
        user = self.request.user
        
        # Superadmins can use the assignment serializer for create/update
        if (self.action in ['create', 'update', 'partial_update'] and 
            (user.is_staff or getattr(user, 'role', None) == 'superadmin')):
            return FacilityAccessAssignmentSerializer
        
        return FacilityAccessSerializer
    
    @action(detail=False, methods=['post'])
    def request_access(self, request):
        """Allow users to request access to a facility"""
        serializer = FacilityAccessRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Check if access already exists
            existing_access = FacilityAccess.objects.filter(
                user=request.user,
                facility=serializer.validated_data['facility']
            ).first()
            
            if existing_access:
                return Response(
                    {'error': 'Access request already exists for this facility'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create new access request
            access = serializer.save(user=request.user, status='pending')
            return Response(
                FacilityAccessSerializer(access).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'])
    def approve_access(self, request, pk=None):
        """Allow admins to approve access requests"""
        if not (request.user.is_staff or getattr(request.user, 'role', None) in ['superadmin', 'admin']):
            return Response(
                {'error': 'Only admins can approve access requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        access = self.get_object()
        serializer = FacilityAccessApprovalSerializer(access, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(FacilityAccessSerializer(access).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_access(self, request):
        """Get current user's approved facility access"""
        access_list = FacilityAccess.objects.filter(user=request.user, status='approved')
        serializer = FacilityAccessSerializer(access_list, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_requests(self, request):
        """Get pending access requests (admin only)"""
        if not (request.user.is_staff or getattr(request.user, 'role', None) in ['superadmin', 'admin']):
            return Response(
                {'error': 'Access denied: Only admin users can view pending facility access requests. If you believe this is an error, please contact your system administrator.'},
                status=status.HTTP_403_FORBIDDEN
            )
        pending_requests = FacilityAccess.objects.filter(status='pending')
        serializer = FacilityAccessSerializer(pending_requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def assign_access(self, request):
        """Allow superadmins to directly assign facility access"""
        if not (request.user.is_staff or getattr(request.user, 'role', None) == 'superadmin'):
            return Response(
                {'error': 'Only superadmins can assign facility access'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = FacilityAccessAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            # Check if access already exists
            existing_access = FacilityAccess.objects.filter(
                user=serializer.validated_data['user'],
                facility=serializer.validated_data['facility']
            ).first()
            
            if existing_access:
                # Update existing access
                updated_access = FacilityAccessAssignmentSerializer(existing_access, data=request.data, partial=True)
                if updated_access.is_valid():
                    updated_access.save()
                    return Response(updated_access.data)
                return Response(updated_access.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Create new access
                access = serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def remove_access(self, request):
        """Allow superadmins to remove facility access"""
        if not (request.user.is_staff or getattr(request.user, 'role', None) == 'superadmin'):
            return Response(
                {'error': 'Only superadmins can remove facility access'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user')
        facility_id = request.data.get('facility')
        
        if not user_id or not facility_id:
            return Response(
                {'error': 'Both user and facility IDs are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            access = FacilityAccess.objects.get(user_id=user_id, facility_id=facility_id)
            access.delete()
            return Response({'message': 'Access removed successfully'})
        except FacilityAccess.DoesNotExist:
            return Response(
                {'error': 'Access record not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Override permissions for specific actions"""
        if self.action in ['login', 'register']:
            return [AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        user = self.request.user
        
        # Superadmins and admins can see all users
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            return User.objects.all()
        
        # Regular users can only see themselves
        return User.objects.filter(id=user.id)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Allow unauthenticated users to register"""
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Allow unauthenticated users to login"""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        if user:
            # AUTOMATIC FACILITY ACCESS FOR ADMINS
            from .models import FacilityAccess
            from residents.models import Facility
            role = getattr(user, 'role', None)
            if user.is_staff or role in ['admin', 'superadmin']:
                all_facilities = Facility.objects.all()
                for facility in all_facilities:
                    fa, created = FacilityAccess.objects.get_or_create(
                        user=user,
                        facility=facility,
                        defaults={
                            'role': 'superadmin' if role == 'superadmin' else 'admin',
                            'status': 'approved',
                        }
                    )
                    # If exists but not approved or wrong role, update
                    if not created:
                        update = False
                        if fa.status != 'approved':
                            fa.status = 'approved'
                            update = True
                        if (role == 'superadmin' and fa.role != 'superadmin') or (role != 'superadmin' and fa.role != 'admin'):
                            fa.role = 'superadmin' if role == 'superadmin' else 'admin'
                            update = True
                        if update:
                            fa.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        else:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
