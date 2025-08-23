from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Staff(models.Model):
    ROLE_CHOICES = [
        ('cna', 'Certified Nursing Assistant'),
        ('lpn', 'Licensed Practical Nurse'),
        ('rn', 'Registered Nurse'),
        ('cna_float', 'CNA Float'),
        ('med_tech', 'Medication Technician'),
        ('caregiver', 'Caregiver'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave'),
        ('terminated', 'Terminated'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    employee_id = models.CharField(max_length=50, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    hire_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    max_hours = models.PositiveIntegerField(default=40, validators=[MinValueValidator(1), MaxValueValidator(168)])
    notes = models.TextField(blank=True)
    facility = models.ForeignKey('residents.Facility', on_delete=models.CASCADE, related_name='staff')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Staff"
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class ShiftTemplate(models.Model):
    SHIFT_TYPE_CHOICES = [
        ('day', 'Day'),
        ('swing', 'Swing'),
        ('noc', 'NOC'),
        ('custom', 'Custom'),
    ]
    
    template_name = models.CharField(max_length=100)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPE_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DecimalField(max_digits=4, decimal_places=2, help_text="Duration in hours")
    required_staff = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(20)])
    is_active = models.BooleanField(default=True)
    facility = models.ForeignKey('residents.Facility', on_delete=models.CASCADE, related_name='shift_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['shift_type', 'start_time']
        unique_together = ['facility', 'template_name']
    
    def __str__(self):
        return f"{self.template_name} ({self.get_shift_type_display()})"


class Shift(models.Model):
    date = models.DateField()
    shift_template = models.ForeignKey(ShiftTemplate, on_delete=models.CASCADE, related_name='shifts')
    facility = models.ForeignKey('residents.Facility', on_delete=models.CASCADE, related_name='shifts')
    required_staff_count = models.PositiveIntegerField(default=1)
    required_staff_role = models.CharField(max_length=20, default='cna')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'shift_template__start_time']
        unique_together = ['facility', 'date', 'shift_template']
    
    def __str__(self):
        return f"{self.shift_template.template_name} - {self.date}"
    
    @property
    def shift_type(self):
        return self.shift_template.shift_type
    
    @property
    def start_time(self):
        return self.shift_template.start_time
    
    @property
    def end_time(self):
        return self.shift_template.end_time
    
    @property
    def duration(self):
        return self.shift_template.duration


class StaffAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='assignments')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['shift__date', 'shift__shift_template__start_time']
        unique_together = ['staff', 'shift']
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.shift}"
    
    def save(self, *args, **kwargs):
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        super().save(*args, **kwargs)


class StaffAvailability(models.Model):
    AVAILABILITY_STATUS_CHOICES = [
        ('available', 'Available'),
        ('no_overtime', 'No Overtime'),
        ('limited', 'Limited Hours'),
        ('unavailable', 'Unavailable'),
    ]
    
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS_CHOICES, default='available')
    max_hours = models.PositiveIntegerField(default=8, validators=[MinValueValidator(1), MaxValueValidator(24)])
    preferred_start_time = models.TimeField(null=True, blank=True)
    preferred_end_time = models.TimeField(null=True, blank=True)
    preferred_shift_types = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    facility = models.ForeignKey('residents.Facility', on_delete=models.CASCADE, related_name='staff_availability')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date', 'staff__last_name']
        unique_together = ['staff', 'date', 'facility']
        verbose_name_plural = "Staff Availability"
    
    def __str__(self):
        return f"{self.staff.full_name} - {self.date} ({self.get_availability_status_display()})"


class AIInsight(models.Model):
    facility = models.ForeignKey('residents.Facility', on_delete=models.CASCADE, related_name='ai_insights')
    date = models.DateField()
    total_residents = models.PositiveIntegerField()
    total_care_hours = models.DecimalField(max_digits=6, decimal_places=2)
    avg_acuity_score = models.DecimalField(max_digits=3, decimal_places=2)
    staffing_efficiency = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    low_acuity_count = models.PositiveIntegerField(default=0)
    medium_acuity_count = models.PositiveIntegerField(default=0)
    high_acuity_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['facility', 'date']
    
    def __str__(self):
        return f"AI Insights - {self.facility.name} - {self.date}"


class AIRecommendation(models.Model):
    facility = models.ForeignKey('residents.Facility', on_delete=models.CASCADE, related_name='ai_recommendations')
    date = models.DateField()
    shift_type = models.CharField(max_length=20)
    care_hours = models.DecimalField(max_digits=5, decimal_places=2)
    required_staff = models.PositiveIntegerField()
    resident_count = models.PositiveIntegerField()
    confidence = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date', 'shift_type']
        unique_together = ['facility', 'date', 'shift_type']
    
    def __str__(self):
        return f"AI Rec - {self.facility.name} - {self.date} {self.shift_type} ({self.confidence}%)"
