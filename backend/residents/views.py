from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Resident, Facility, FacilitySection
from .serializers import ResidentSerializer, FacilitySerializer, FacilitySectionDetailSerializer
import csv
import io
import pandas as pd
import logging
from django.db.models import Sum
from adls.models import ADL
import datetime
from users.models import FacilityAccess
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)



class ResidentViewSet(viewsets.ModelViewSet):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer

    def get_queryset(self):
        user = self.request.user
        # Superadmins and admins see all residents
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            return Resident.objects.all()

        # Get approved facility IDs for this user
        approved_facility_ids = FacilityAccess.objects.filter(
            user=user,
            status='approved'
        ).values_list('facility_id', flat=True)

        # Get all sections in those facilities
        allowed_sections = FacilitySection.objects.filter(facility_id__in=approved_facility_ids)

        # Only residents in allowed sections
        return Resident.objects.filter(facility_section__in=allowed_sections)

    def list(self, request, *args, **kwargs):
        """Custom list method to handle facility_id filtering"""
        facility_id = request.query_params.get('facility_id')
        
        if facility_id:
            # Filter by specific facility
            try:
                sections = FacilitySection.objects.filter(facility_id=facility_id)
                residents = Resident.objects.filter(facility_section__in=sections)
                
                # Apply pagination
                page = self.paginate_queryset(residents)
                if page is not None:
                    serializer = self.get_serializer(page, many=True)
                    return self.get_paginated_response(serializer.data)
                
                serializer = self.get_serializer(residents, many=True)
                return Response({
                    'count': residents.count(),
                    'results': serializer.data
                })
                
            except Exception as e:
                logger.error(f"Error filtering residents by facility {facility_id}: {e}")
                return Response({'error': 'Invalid facility ID'}, status=400)
        
        # Default behavior - use get_queryset
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def debug_count(self, request):
        """Debug endpoint to check resident count without authentication"""
        total_residents = Resident.objects.count()
        facility_id = request.query_params.get('facility_id')
        
        if facility_id:
            sections = FacilitySection.objects.filter(facility_id=facility_id)
            residents_in_facility = Resident.objects.filter(facility_section__in=sections).count()
            return Response({
                'total_residents': total_residents,
                'facility_id': facility_id,
                'residents_in_facility': residents_in_facility,
                'sections_in_facility': sections.count(),
                'section_details': [
                    {
                        'id': section.id,
                        'name': section.name,
                        'residents_count': section.residents.count()
                    } for section in sections
                ]
            })
        
        return Response({
            'total_residents': total_residents,
            'message': 'Add ?facility_id=73 to see facility-specific data'
        })

    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export residents to CSV"""
        residents = self.get_queryset()
        
        # Create the CSV file
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Name', 'Status', 'Facility Section', 'Facility ID', 'Facility Name'])
        
        # Write data
        for resident in residents:
            writer.writerow([
                resident.name,
                resident.status,
                resident.facility_section,
                resident.facility_id,
                resident.facility_name,
            ])
        
        # Create the response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="residents.csv"'
        
        return response

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        """Import residents from CSV"""
        logger.info("Starting CSV import")
        if 'file' not in request.FILES:
            logger.error("No file in request.FILES")
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
        file = request.FILES['file']
        logger.info(f"Received file: {file.name}")
        if not file.name.endswith('.csv'):
            logger.error("File is not a CSV")
            return Response({'error': 'File must be a CSV'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Read the CSV file
            logger.info("Reading CSV file")
            df = pd.read_csv(file)
            logger.info(f"CSV columns: {df.columns.tolist()}")
            # Map column names to expected fields
            column_mapping = {
                'ResidentName': 'name',
                'ResidentStatus': 'status',
                'FacilitySectionName': 'facility_section',
                'FacilityID': 'facility_id',
                'FacilityName': 'facility_name'
            }
            required_columns = list(column_mapping.keys())
            if not all(col in df.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in df.columns]
                logger.error(f"Missing required columns: {missing_cols}")
                return Response({
                    'error': f'Missing required columns: {", ".join(missing_cols)}. Required columns are: {", ".join(required_columns)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            unique_residents = df[required_columns].drop_duplicates()
            logger.info(f"Found {len(unique_residents)} unique residents")
            created_count = 0
            updated_count = 0
            for _, row in unique_residents.iterrows():
                # Clean and map the data
                resident_data = {
                    new_key: str(row[old_key]).strip() 
                    for old_key, new_key in column_mapping.items()
                }
                logger.info(f"Processing resident: {resident_data['name']}")
                # Get or create Facility
                facility, _ = Facility.objects.get_or_create(
                    facility_id=resident_data['facility_id'],
                    defaults={'name': resident_data['facility_name']}
                )
                # Get or create FacilitySection
                section, _ = FacilitySection.objects.get_or_create(
                    name=resident_data['facility_section'],
                    facility=facility
                )
                # Try to find existing resident by name and section
                resident, created = Resident.objects.update_or_create(
                    name=resident_data['name'],
                    facility_section=section,
                    defaults={
                        'status': resident_data['status'],
                        'facility_section': section
                    }
                )
                if created:
                    created_count += 1
                    logger.info(f"Created new resident: {resident.name}")
                else:
                    updated_count += 1
                    logger.info(f"Updated existing resident: {resident.name}")
            logger.info(f"Import complete. Created: {created_count}, Updated: {updated_count}")
            return Response({
                'message': f'Successfully imported {created_count} new residents and updated {updated_count} existing residents.'
            })
        except Exception as e:
            logger.error(f"Error during import: {str(e)}", exc_info=True)
            return Response({'error': f'Error importing file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def caregiving_summary(self, request, pk=None):
        resident = self.get_object()
        from adls.models import ADL
        from users.models import FacilityAccess
        
        # Check if user has access to this resident's facility
        user = request.user
        
        # Superadmins and admins see all ADLs
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            adls = ADL.objects.filter(resident=resident, is_deleted=False)
        else:
            # For anonymous users, return empty data
            if user.is_anonymous:
                return Response({
                    'per_shift': [{'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']],
                    'per_day': [{'day': day, 'hours': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                })
            
            # Get approved facility IDs for this user
            approved_facility_ids = FacilityAccess.objects.filter(
                user=user,
                status='approved'
            ).values_list('facility_id', flat=True)

            # Check if user has access to this resident's facility
            if resident.facility_section.facility.id not in approved_facility_ids:
                return Response({'error': 'Access denied to this resident'}, status=403)

            adls = ADL.objects.filter(resident=resident, is_deleted=False)
        
        shift_map = {
            'Shift1': 'Day',
            'Shift2': 'Swing',
            'Shift3': 'NOC',
        }
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_prefixes = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
        per_shift = [
            {'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in days
        ]
        
        # Use resident total shift times for chart calculation (like Oregon ABST)
        resident_total_times = resident.total_shift_times or {}
        for i, prefix in enumerate(day_prefixes):
            for shift_num, shift_name in shift_map.items():
                col = f'ResidentTotal{prefix}{shift_num}Time'
                minutes = resident_total_times.get(col, 0)
                per_shift[i][shift_name] += minutes / 60.0
        for s in per_shift:
            for shift in ['Day', 'Swing', 'NOC']:
                s[shift] = round(s[shift], 2)
        per_day = [
            {'day': s['day'], 'hours': round(s['Day'] + s['Swing'] + s['NOC'], 2)}
            for s in per_shift
        ]
        return Response({
            'per_shift': per_shift,
            'per_day': per_day
        })

from rest_framework.permissions import AllowAny

class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.all()
    serializer_class = FacilitySerializer
    permission_classes = [AllowAny]  # Allow unauthenticated access for facility listing

    def get_queryset(self):
        user = self.request.user
        # Superadmins and admins see all facilities
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            return Facility.objects.all()

        # For anonymous users, show all facilities (for access request)
        if user.is_anonymous:
            return Facility.objects.all()

        # Get approved facility IDs for this user
        approved_facility_ids = FacilityAccess.objects.filter(
            user=user,
            status='approved'
        ).values_list('facility_id', flat=True)

        # If user has no approved access, show all facilities (for access request)
        if not approved_facility_ids:
            return Facility.objects.all()

        return Facility.objects.filter(id__in=approved_facility_ids)

    def update(self, request, *args, **kwargs):
        print('DEBUG Facility update payload:', request.data)
        response = super().update(request, *args, **kwargs)
        if response.status_code == 400:
            print('DEBUG Facility update error:', response.data)
        return response

    @action(detail=True, methods=['get'])
    def caregiving_summary(self, request, pk=None):
        facility = self.get_object()
        sections = facility.sections.all()
        residents = Resident.objects.filter(facility_section__in=sections)
        
        # Filter ADLs based on user permissions
        user = request.user
        from adls.models import ADL
        from users.models import FacilityAccess
        
        # Superadmins and admins see all ADLs
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            adls = ADL.objects.filter(resident__in=residents, is_deleted=False)
        else:
            # For anonymous users, return empty data
            if user.is_anonymous:
                return Response({
                    'per_shift': [{'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']],
                    'per_day': [{'day': day, 'hours': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                })
            
            # Get approved facility IDs for this user
            approved_facility_ids = FacilityAccess.objects.filter(
                user=user,
                status='approved'
            ).values_list('facility_id', flat=True)

            # Only show data if user has access to this facility
            if facility.id not in approved_facility_ids:
                return Response({'error': 'Access denied to this facility'}, status=403)

            adls = ADL.objects.filter(resident__in=residents, is_deleted=False)
        
        shift_map = {
            'Shift1': 'Day',
            'Shift2': 'Swing',
            'Shift3': 'NOC',
        }
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_prefixes = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
        per_shift = [
            {'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in days
        ]
        
        # Use resident total shift times for chart calculation (like Oregon ABST)
        for resident in residents:
            resident_total_times = resident.total_shift_times or {}
            for i, prefix in enumerate(day_prefixes):
                for shift_num, shift_name in shift_map.items():
                    col = f'ResidentTotal{prefix}{shift_num}Time'
                    minutes = resident_total_times.get(col, 0)
                    per_shift[i][shift_name] += minutes / 60.0
        for s in per_shift:
            for shift in ['Day', 'Swing', 'NOC']:
                s[shift] = round(s[shift], 2)
        per_day = [
            {'day': s['day'], 'hours': round(s['Day'] + s['Swing'] + s['NOC'], 2)}
            for s in per_shift
        ]
        return Response({
            'per_shift': per_shift,
            'per_day': per_day
        })

class FacilitySectionViewSet(viewsets.ModelViewSet):
    queryset = FacilitySection.objects.all()
    serializer_class = FacilitySectionDetailSerializer

    @action(detail=True, methods=['get'])
    def caregiving_summary(self, request, pk=None):
        section = self.get_object()
        residents = section.residents.all()
        
        # Check if user has access to this section's facility
        user = request.user
        from adls.models import ADL
        from users.models import FacilityAccess
        
        # Superadmins and admins see all ADLs
        if user.is_staff or getattr(user, 'role', None) in ['superadmin', 'admin']:
            adls = ADL.objects.filter(resident__in=residents, is_deleted=False)
        else:
            # For anonymous users, return empty data
            if user.is_anonymous:
                return Response({
                    'per_shift': [{'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']],
                    'per_day': [{'day': day, 'hours': 0} for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
                })
            
            # Get approved facility IDs for this user
            approved_facility_ids = FacilityAccess.objects.filter(
                user=user,
                status='approved'
            ).values_list('facility_id', flat=True)

            # Check if user has access to this section's facility
            if section.facility.id not in approved_facility_ids:
                return Response({'error': 'Access denied to this section'}, status=403)

            adls = ADL.objects.filter(resident__in=residents, is_deleted=False)
        
        # Map shift columns to readable names
        shift_map = {
            'Shift1': 'Day',
            'Shift2': 'Swing',
            'Shift3': 'NOC',
        }
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_prefixes = ['Mon', 'Tues', 'Wed', 'Thurs', 'Fri', 'Sat', 'Sun']
        # Initialize summary structure
        per_shift = [
            {'day': day, 'Day': 0, 'Swing': 0, 'NOC': 0} for day in days
        ]
        
        # Use resident total shift times for chart calculation (like Oregon ABST)
        for resident in residents:
            resident_total_times = resident.total_shift_times or {}
            for i, prefix in enumerate(day_prefixes):
                for shift_num, shift_name in shift_map.items():
                    col = f'ResidentTotal{prefix}{shift_num}Time'
                    minutes = resident_total_times.get(col, 0)
                    per_shift[i][shift_name] += minutes / 60.0  # convert to hours
        # Optionally round to 2 decimals
        for s in per_shift:
            for shift in ['Day', 'Swing', 'NOC']:
                s[shift] = round(s[shift], 2)
        # Simple per-day total
        per_day = [
            {'day': s['day'], 'hours': round(s['Day'] + s['Swing'] + s['NOC'], 2)}
            for s in per_shift
        ]
        return Response({
            'per_shift': per_shift,
            'per_day': per_day
        })
