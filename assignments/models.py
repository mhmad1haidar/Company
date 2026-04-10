from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class AssignmentStatusHistory(models.Model):
    """Track status changes for assignments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey('WorkAssignment', on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Assignment Status History'
        verbose_name_plural = 'Assignment Status Histories'
    
    def __str__(self):
        return f"{self.assignment.codice_nigit}: {self.old_status} -> {self.new_status} by {self.changed_by}"

class WorkAssignment(models.Model):
    """
    Work Assignment model for assigning interventions to employees
    """
    
    # Status choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('not_worked', 'Not Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Internal fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments_created')
    
    # Link to Intervention
    intervention = models.ForeignKey(
        'interventions.Intervention',
        on_delete=models.CASCADE,
        related_name='work_assignments',
        verbose_name="Intervention"
    )
    
    # Assignment details
    codice_nigit = models.CharField(max_length=50, verbose_name="Codice NIGIT", db_index=True)
    assigned_to = models.ManyToManyField(
        User,
        related_name='work_assignments',
        verbose_name="Assigned To"
    )
    vehicle = models.ForeignKey(
        'fleet.Car',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_assignments',
        verbose_name="Vehicle"
    )
    assignment_note = models.TextField(verbose_name="Assignment Note", help_text="Instructions for the employee")
    
    # Site information (auto-filled from site data)
    site_address = models.TextField(verbose_name="Site Address", blank=True)
    site_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=8, 
        verbose_name="Site Latitude", 
        null=True, 
        blank=True
    )
    site_longitude = models.DecimalField(
        max_digits=11, 
        decimal_places=8, 
        verbose_name="Site Longitude", 
        null=True, 
        blank=True
    )
    
    # Status and dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status",
        db_index=True
    )
    assigned_date = models.DateTimeField(verbose_name="Assigned Date", auto_now_add=True)
    scheduled_date = models.DateTimeField(
        verbose_name="Scheduled Date",
        null=True,
        blank=True,
        help_text="When the work should be performed"
    )
    completed_date = models.DateTimeField(
        verbose_name="Completed Date",
        null=True,
        blank=True
    )
    completion_note = models.TextField(
        verbose_name="Completion Note",
        blank=True,
        help_text="Notes about work completion"
    )
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_assignments',
        verbose_name="Completed By"
    )
    work_performed = models.BooleanField(
        default=True,
        verbose_name="Work Performed",
        help_text="Indicates if the work was actually completed"
    )
    
    class Meta:
        verbose_name = "Work Assignment"
        verbose_name_plural = "Work Assignments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'assigned_date']),
            models.Index(fields=['codice_nigit']),
        ]
    
    def __str__(self):
        assigned_names = ", ".join([u.get_full_name() or u.username for u in self.assigned_to.all()[:3]])
        if self.assigned_to.count() > 3:
            assigned_names += "..."
        return f"{self.codice_nigit} → {assigned_names or 'Unassigned'}"
    
    @property
    def client_name(self):
        """Get client name from intervention"""
        return self.intervention.cliente if self.intervention else ""
    
    @property
    def intervention_name(self):
        """Get intervention name from intervention"""
        return self.intervention.nome if self.intervention else ""
    
    @property
    def is_overdue(self):
        """Check if assignment is overdue"""
        if self.scheduled_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.scheduled_date
        return False
    
    @property
    def days_since_assigned(self):
        """Calculate days since assignment"""
        return (timezone.now() - self.assigned_date).days
    
    def save(self, *args, **kwargs):
        """Auto-fill site data from intervention and update completed date"""
        if self.intervention:
            # Auto-fill codice_nigit from intervention
            self.codice_nigit = self.intervention.codice_nigit
            
            # Try to find site data and auto-fill address/coordinates
            self._auto_fill_site_data()
        
        # Auto-set completed date when status changes to completed
        if self.status == 'completed' and not self.completed_date:
            self.completed_date = timezone.now()
        elif self.status != 'completed':
            self.completed_date = None
            
        super().save(*args, **kwargs)
    
    def mark_complete(self, user, completion_note="", work_performed=True):
        """Mark assignment as completed by user"""
        self.status = 'completed'
        self.completed_by = user
        self.completed_date = timezone.now()
        self.work_performed = work_performed
        if completion_note:
            self.completion_note = completion_note
        self.save()
    
    def _auto_fill_site_data(self):
        """Auto-fill site data from TelecomSite or intervention data"""
        if not self.intervention:
            return
            
        # Try to match with TelecomSite using different fields
        site = None
        
        # Try international_code first
        if self.intervention.international_code:
            from interventions.models import TelecomSite
            site = TelecomSite.objects.filter(
                site_code__iexact=self.intervention.international_code
            ).first()
        
        # Try codice_sito if no match
        if not site and self.intervention.codice_sito:
            from interventions.models import TelecomSite
            site = TelecomSite.objects.filter(
                site_code__iexact=self.intervention.codice_sito
            ).first()
        
        # Try matching by site name if still no match
        if not site and self.intervention.nome:
            from interventions.models import TelecomSite
            site = TelecomSite.objects.filter(
                site_name__icontains=self.intervention.nome
            ).first()
        
        # Fill site data if found
        if site:
            self.site_address = f"{site.address}, {site.city or ''}, {site.province or ''}".strip(", ")
            self.site_latitude = site.latitude
            self.site_longitude = site.longitude
        else:
            # Fallback to intervention data if available
            # Note: Intervention model doesn't have address fields, so we'll leave empty
            pass
    
    def get_maps_url(self):
        """Get Google Maps URL for the site location"""
        if self.site_latitude and self.site_longitude:
            return f"https://www.google.com/maps?q={self.site_latitude},{self.site_longitude}"
        elif self.site_address:
            return f"https://www.google.com/maps/search/?api=1&query={self.site_address.replace(' ', '+')}"
        return "#"
    
    def get_directions_url(self):
        """Get Google Maps directions URL"""
        if self.site_latitude and self.site_longitude:
            return f"https://www.google.com/maps/dir/?api=1&destination={self.site_latitude},{self.site_longitude}"
        elif self.site_address:
            return f"https://www.google.com/maps/dir/?api=1&destination={self.site_address.replace(' ', '+')}"
        return "#"
