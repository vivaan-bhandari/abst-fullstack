from django.contrib import admin
from .models import Staff, ShiftTemplate, Shift, StaffAssignment, StaffAvailability, AIInsight, AIRecommendation


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'employee_id', 'role', 'status', 'facility', 'hire_date', 'max_hours']
    list_filter = ['role', 'status', 'facility', 'hire_date']
    search_fields = ['first_name', 'last_name', 'employee_id', 'email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email', 'employee_id')
        }),
        ('Employment Details', {
            'fields': ('role', 'hire_date', 'status', 'max_hours')
        }),
        ('Additional Information', {
            'fields': ('notes', 'facility')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_name', 'shift_type', 'start_time', 'end_time', 'duration', 'required_staff', 'is_active', 'facility']
    list_filter = ['shift_type', 'is_active', 'facility']
    search_fields = ['template_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['shift_type', 'start_time']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('template_name', 'shift_type', 'facility')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('Staffing', {
            'fields': ('required_staff', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['date', 'shift_template', 'facility', 'required_staff_count', 'required_staff_role']
    list_filter = ['date', 'shift_template__shift_type', 'facility']
    search_fields = ['shift_template__template_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', 'shift_template__start_time']
    
    fieldsets = (
        ('Shift Information', {
            'fields': ('date', 'shift_template', 'facility')
        }),
        ('Staffing Requirements', {
            'fields': ('required_staff_count', 'required_staff_role')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StaffAssignment)
class StaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ['staff', 'shift', 'status', 'assigned_at', 'confirmed_at']
    list_filter = ['status', 'assigned_at', 'shift__facility']
    search_fields = ['staff__first_name', 'staff__last_name', 'shift__shift_template__template_name']
    readonly_fields = ['assigned_at']
    ordering = ['-assigned_at']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('staff', 'shift', 'status')
        }),
        ('Timing', {
            'fields': ('assigned_at', 'confirmed_at')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StaffAvailability)
class StaffAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'availability_status', 'max_hours', 'facility']
    list_filter = ['availability_status', 'date', 'facility']
    search_fields = ['staff__first_name', 'staff__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-date', 'staff__last_name']
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('staff', 'facility')
        }),
        ('Availability Details', {
            'fields': ('date', 'availability_status', 'max_hours')
        }),
        ('Preferences', {
            'fields': ('preferred_start_time', 'preferred_end_time', 'preferred_shift_types')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['facility', 'date', 'total_residents', 'total_care_hours', 'avg_acuity_score', 'staffing_efficiency']
    list_filter = ['date', 'facility']
    search_fields = ['facility__name']
    readonly_fields = ['created_at']
    ordering = ['-date']
    
    fieldsets = (
        ('Facility Information', {
            'fields': ('facility', 'date')
        }),
        ('Resident Metrics', {
            'fields': ('total_residents', 'total_care_hours', 'avg_acuity_score')
        }),
        ('Staffing Metrics', {
            'fields': ('staffing_efficiency',)
        }),
        ('Acuity Distribution', {
            'fields': ('low_acuity_count', 'medium_acuity_count', 'high_acuity_count')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ['facility', 'date', 'shift_type', 'care_hours', 'required_staff', 'resident_count', 'confidence', 'applied']
    list_filter = ['date', 'shift_type', 'facility', 'applied']
    search_fields = ['facility__name']
    readonly_fields = ['created_at']
    ordering = ['-date', 'shift_type']
    
    fieldsets = (
        ('Recommendation Details', {
            'fields': ('facility', 'date', 'shift_type')
        }),
        ('Staffing Requirements', {
            'fields': ('care_hours', 'required_staff', 'resident_count')
        }),
        ('AI Analysis', {
            'fields': ('confidence', 'applied')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
