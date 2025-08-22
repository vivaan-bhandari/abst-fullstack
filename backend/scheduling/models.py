from django.db import models
from django.contrib.auth.models import User
from residents.models import Facility, FacilitySection
from adls.models import ADL

class Staff(models.Model):
    """Staff member model for scheduling"""
    ROLE_CHOICES = [
        ('rn', 'Registered Nurse'),
        ('lpn', 'Licensed Practical Nurse'),
        ('cna', 'Certified Nursing Assistant'),
        ('med_tech', 'Medication Technician'),
        ('aide', 'Personal Care Aide'),
        ('supervisor', 'Supervisor'),
        ('admin', 'Administrator'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    hire_date = models.DateField()
    facility = models.ForeignKey('residents.Facility', on_delete=models.CASCADE, related_name='staff_members', null=True, blank=True)
    certifications = models.JSONField(default=list, blank=True)  # List of certifications
    skills = models.JSONField(default=list, blank=True)  # List of skills
    max_hours_per_week = models.PositiveIntegerField(default=40)
    preferred_shifts = models.JSONField(default=list, blank=True)  # List of preferred shift types
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Staff"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class ShiftTemplate(models.Model):
    """Template for creating shifts"""
    SHIFT_TYPE_CHOICES = [
        ('day', 'Day'),
        ('swing', 'Swing'),
        ('noc', 'NOC'),
    ]
    
    name = models.CharField(max_length=100)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPE_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='shift_templates')
    required_staff_count = models.PositiveIntegerField(default=1)
    required_roles = models.JSONField(default=list, blank=True)  # List of required roles
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.name} ({self.get_shift_type_display()}) - {self.facility.name}"

class Shift(models.Model):
    """Individual shift instance"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    date = models.DateField()
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.CASCADE, related_name='shifts')
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='shifts')
    section = models.ForeignKey(FacilitySection, on_delete=models.CASCADE, related_name='shifts', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    actual_start_time = models.TimeField(null=True, blank=True)
    actual_end_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'shift_template__start_time']
        unique_together = ['date', 'shift_template', 'facility']
    
    def __str__(self):
        return f"{self.shift_template.name} - {self.date} - {self.facility.name}"
    
    @property
    def is_overstaffed(self):
        return self.staff_assignments.count() > self.shift_template.required_staff_count
    
    @property
    def is_understaffed(self):
        return self.staff_assignments.count() < self.shift_template.required_staff_count

class StaffAssignment(models.Model):
    """Assignment of staff to shifts"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assignments')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='staff_assignments')
    assigned_role = models.CharField(max_length=20, choices=Staff.ROLE_CHOICES)
    clock_in_time = models.DateTimeField(null=True, blank=True)
    clock_out_time = models.DateTimeField(null=True)
    actual_hours_worked = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'shift']
        ordering = ['shift__date', 'shift__shift_template__start_time']
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.shift}"

class AcuityBasedStaffing(models.Model):
    """Links ADL data to staffing requirements"""
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='acuity_staffing')
    total_care_hours_needed = models.DecimalField(max_digits=6, decimal_places=2)
    high_acuity_residents = models.PositiveIntegerField(default=0)
    medium_acuity_residents = models.PositiveIntegerField(default=0)
    low_acuity_residents = models.PositiveIntegerField(default=0)
    recommended_staff_count = models.PositiveIntegerField()
    recommended_skill_mix = models.JSONField(default=dict)  # Dict of role:count
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Acuity Based Staffing"
    
    def __str__(self):
        return f"Acuity Staffing - {self.shift} - {self.recommended_staff_count} staff needed"

class StaffAvailability(models.Model):
    """Staff availability and preferences"""
    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
        ('preferred', 'Preferred'),
        ('limited', 'Limited Hours'),
        ('overtime_ok', 'Overtime OK'),
        ('no_overtime', 'No Overtime'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available')
    is_available = models.BooleanField(default=True)  # Keep for backward compatibility
    preferred_start_time = models.TimeField(null=True, blank=True)
    preferred_end_time = models.TimeField(null=True, blank=True)
    max_hours = models.PositiveIntegerField(null=True, blank=True)
    preferred_shifts = models.JSONField(default=list, blank=True)  # List of preferred shift types
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['staff', 'date']
        ordering = ['date']
        verbose_name_plural = "Staff Availability"
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.date} - {self.get_availability_status_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-update is_available based on availability_status
        if self.availability_status in ['available', 'preferred', 'overtime_ok']:
            self.is_available = True
        else:
            self.is_available = False
        super().save(*args, **kwargs)
