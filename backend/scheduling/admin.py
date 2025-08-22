from django.contrib import admin
from .models import (
    Staff, ShiftTemplate, Shift, StaffAssignment, 
    AcuityBasedStaffing, StaffAvailability
)

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'role', 'status', 'facility', 'hire_date', 'max_hours_per_week']
    list_filter = ['role', 'status', 'facility', 'hire_date']
    search_fields = ['employee_id', 'first_name', 'last_name', 'user__email', 'facility__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'first_name', 'last_name', 'role', 'status', 'facility')
        }),
        ('Employment Details', {
            'fields': ('hire_date', 'max_hours_per_week')
        }),
        ('Skills & Preferences', {
            'fields': ('certifications', 'skills', 'preferred_shifts', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'shift_type', 'facility', 'start_time', 'end_time', 'duration_hours', 'required_staff_count', 'is_active']
    list_filter = ['shift_type', 'facility', 'is_active']
    search_fields = ['name', 'facility__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'shift_type', 'facility')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration_hours')
        }),
        ('Staffing Requirements', {
            'fields': ('required_staff_count', 'required_roles')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['date', 'shift_template', 'facility', 'section', 'status', 'is_understaffed', 'is_overstaffed']
    list_filter = ['date', 'status', 'facility', 'shift_template__shift_type']
    search_fields = ['facility__name', 'shift_template__name']
    readonly_fields = ['created_at', 'updated_at', 'is_understaffed', 'is_overstaffed']
    fieldsets = (
        ('Shift Details', {
            'fields': ('date', 'shift_template', 'facility', 'section')
        }),
        ('Status & Timing', {
            'fields': ('status', 'actual_start_time', 'actual_end_time')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(StaffAssignment)
class StaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ['staff', 'shift', 'assigned_role', 'clock_in_time', 'clock_out_time', 'actual_hours_worked']
    list_filter = ['assigned_role', 'shift__status', 'shift__facility']
    search_fields = ['staff__first_name', 'staff__last_name', 'shift__facility__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Assignment', {
            'fields': ('staff', 'shift', 'assigned_role')
        }),
        ('Time Tracking', {
            'fields': ('clock_in_time', 'clock_out_time', 'actual_hours_worked')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AcuityBasedStaffing)
class AcuityBasedStaffingAdmin(admin.ModelAdmin):
    list_display = ['shift', 'total_care_hours_needed', 'recommended_staff_count', 'high_acuity_residents', 'medium_acuity_residents', 'low_acuity_residents']
    list_filter = ['shift__facility', 'shift__date']
    search_fields = ['shift__facility__name', 'shift__shift_template__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Shift Information', {
            'fields': ('shift',)
        }),
        ('Care Requirements', {
            'fields': ('total_care_hours_needed', 'high_acuity_residents', 'medium_acuity_residents', 'low_acuity_residents')
        }),
        ('Staffing Recommendations', {
            'fields': ('recommended_staff_count', 'recommended_skill_mix')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'availability_status', 'is_available', 'preferred_start_time', 'preferred_end_time', 'max_hours', 'facility']
    list_filter = ['availability_status', 'is_available', 'date', 'staff__role', 'staff__facility']
    search_fields = ['staff__first_name', 'staff__last_name', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', 'staff__last_name']
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('staff', 'date')
        }),
        ('Availability', {
            'fields': ('availability_status', 'is_available')
        }),
        ('Preferences', {
            'fields': ('preferred_start_time', 'preferred_end_time', 'max_hours', 'preferred_shifts')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )
    
    def facility(self, obj):
        return obj.staff.facility.name if obj.staff.facility else 'N/A'
    facility.short_description = 'Facility'
    
    readonly_fields = ['created_at', 'updated_at']
