from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
from django.core.validators import RegexValidator
import os
from django.utils import timezone

def employee_document_path(instance, filename):
    """Generate upload path for employee documents: employee_documents/user_id_username/YYYY/MM/filename"""
    user_id = instance.employee.id
    username = instance.employee.username
    year = timezone.now().year
    month = timezone.now().month
    # Get file extension
    ext = os.path.splitext(filename)[1]
    # Create safe filename
    safe_filename = f"doc_{instance.id if instance.id else 'new'}{ext}"
    return f'employee_documents/{user_id}_{username}/{year:04d}/{month:02d}/{safe_filename}'


class UserManager(DjangoUserManager):
    """
    Ensures new users get a sensible default `role`.

    `date_joined` is inherited from AbstractUser and is set automatically
    when the account is created; we do not redefine it.
    """

    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "employee")
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model.

    `date_joined` comes from AbstractUser (registration / account creation time).
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        EMPLOYEE = "employee", "Employee"
        EX_EMPLOYEE = "ex_employee", "Ex-Employee"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        db_index=True,
    )
    employee_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    department = models.CharField(max_length=128, blank=True)
    job_title = models.CharField(max_length=128, blank=True)
    dark_mode = models.BooleanField(default=False, help_text="Enable dark mode for user interface")

    objects = UserManager()

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username


class Department(models.Model):
    """Department model for organizational structure"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Department"
        verbose_name_plural = "Departments"
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class EmployeeProfile(models.Model):
    """Extended employee profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other'),
            ('prefer_not_to_say', 'Prefer not to say')
        ],
        blank=True
    )
    blood_group = models.CharField(
        max_length=5,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
            ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')
        ],
        blank=True
    )
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    personal_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    work_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    
    # Address Information
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Professional Information
    hire_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ('full_time', 'Full Time'),
            ('part_time', 'Part Time'),
            ('contract', 'Contract'),
            ('intern', 'Intern'),
            ('consultant', 'Consultant')
        ],
        default='full_time'
    )
    work_location = models.CharField(max_length=100, blank=True)
    reporting_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    
    # Financial Information
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Additional Information
    nationality = models.CharField(max_length=50, blank=True)
    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('single', 'Single'),
            ('married', 'Married'),
            ('divorced', 'Divorced'),
            ('widowed', 'Widowed')
        ],
        blank=True
    )
    passport_number = models.CharField(max_length=50, blank=True)
    visa_status = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Employee Profile"
        verbose_name_plural = "Employee Profiles"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Profile"


class EmployeeDocument(models.Model):
    """Employee documents management"""
    DOCUMENT_TYPES = [
        ('resume', 'Resume/CV'),
        ('contract', 'Employment Contract'),
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('education', 'Education Certificate'),
        ('experience', 'Experience Certificate'),
        ('passport', 'Passport'),
        ('visa', 'Visa'),
        ('medical', 'Medical Certificate'),
        ('police_verification', 'Police Verification'),
        ('salary_slip', 'Salary Slip'),
        ('offer_letter', 'Offer Letter'),
        ('joining_letter', 'Joining Letter'),
        ('relieving_letter', 'Relieving Letter'),
        ('other', 'Other')
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=employee_document_path)
    upload_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-upload_date']
        verbose_name = "Employee Document"
        verbose_name_plural = "Employee Documents"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.title}"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False


class EmployeeSkill(models.Model):
    """Employee skills and qualifications"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert')
        ]
    )
    years_of_experience = models.IntegerField(null=True, blank=True)
    certification = models.CharField(max_length=200, blank=True)
    certification_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-years_of_experience', 'skill_name']
        verbose_name = "Employee Skill"
        verbose_name_plural = "Employee Skills"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.skill_name}"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False
    
    @property
    def is_expiring_soon(self):
        if self.expiry_date:
            days_until_expiry = (self.expiry_date - timezone.now().date()).days
            return 0 <= days_until_expiry <= 30
        return False


class Certification(models.Model):
    """Professional certifications with expiry tracking"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certifications')
    certification_name = models.CharField(max_length=200)
    certification_number = models.CharField(max_length=100, blank=True)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    certificate_file = models.FileField(upload_to='certifications/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expiry_date']
        verbose_name = "Certification"
        verbose_name_plural = "Certifications"
        indexes = [
            models.Index(fields=['employee', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.certification_name}"
    
    @property
    def is_expired(self):
        return self.expiry_date < timezone.now().date()
    
    @property
    def is_expiring_soon(self):
        days_until_expiry = (self.expiry_date - timezone.now().date()).days
        return 0 <= days_until_expiry <= 30
    
    @property
    def days_until_expiry(self):
        return (self.expiry_date - timezone.now().date()).days


class EmployeeAsset(models.Model):
    """Assets allocated to employees"""
    ASSET_TYPES = [
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop Computer'),
        ('phone', 'Mobile Phone'),
        ('tablet', 'Tablet'),
        ('monitor', 'Monitor'),
        ('keyboard', 'Keyboard'),
        ('mouse', 'Mouse'),
        ('printer', 'Printer'),
        ('scanner', 'Scanner'),
        ('chair', 'Chair'),
        ('desk', 'Desk'),
        ('other', 'Other')
    ]
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assets')
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES)
    asset_name = models.CharField(max_length=200)
    asset_tag = models.CharField(max_length=50, unique=True)
    serial_number = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    allocation_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    is_returned = models.BooleanField(default=False)
    condition = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor')
        ],
        default='good'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-allocation_date']
        verbose_name = "Employee Asset"
        verbose_name_plural = "Employee Assets"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.asset_name}"


class Notification(models.Model):
    """Notification system for users"""

    class NotificationType(models.TextChoices):
        LEAVE_REQUEST = 'leave_request', 'Leave Request'
        LEAVE_APPROVED = 'leave_approved', 'Leave Approved'
        LEAVE_REJECTED = 'leave_rejected', 'Leave Rejected'
        ATTENDANCE_LATE = 'attendance_late', 'Late Check-in'
        ATTENDANCE_ABSENT = 'attendance_absent', 'Absent'
        ATTENDANCE_MISSING_CHECKOUT = 'attendance_missing_checkout', 'Missing Check-out'
        ASSIGNMENT_NEW = 'assignment_new', 'New Assignment'
        ASSIGNMENT_STATUS_CHANGE = 'assignment_status_change', 'Assignment Status Change'
        ASSIGNMENT_DEADLINE = 'assignment_deadline', 'Assignment Deadline'
        INTERVENTION_NEW = 'intervention_new', 'New Intervention'
        INTERVENTION_STATUS_CHANGE = 'intervention_status_change', 'Intervention Status Change'
        SYSTEM = 'system', 'System'

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, help_text='URL to redirect when notification is clicked')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.title}"


class Announcement(models.Model):
    """Announcement/Notice board with priority levels"""

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    target_audience = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Users'),
            ('staff', 'Staff Only'),
            ('managers', 'Managers Only'),
            ('admin', 'Admin Only'),
        ],
        default='all'
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True, help_text='Leave blank for no expiry')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        indexes = [
            models.Index(fields=['-priority', '-created_at']),
            models.Index(fields=['is_active', 'start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"

    @property
    def is_current(self):
        """Check if announcement is currently active based on dates"""
        now = timezone.now()
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return self.is_active


class Message(models.Model):
    """Internal messaging system between employees"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['sender', 'recipient']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.sender.get_full_name()} to {self.recipient.get_full_name()}: {self.subject}"

    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    @property
    def is_reply(self):
        """Check if this is a reply to another message"""
        return self.parent_message is not None


class Widget(models.Model):
    """Customizable dashboard widgets for different user roles"""
    class WidgetType(models.TextChoices):
        ATTENDANCE = "attendance", "Attendance Stats"
        ASSIGNMENTS = "assignments", "Recent Assignments"
        ANNOUNCEMENTS = "announcements", "Announcements"
        MESSAGES = "messages", "Unread Messages"
        LEAVE = "leave", "Leave Balance"
        NOTIFICATIONS = "notifications", "Notifications"
        QUICK_ACTIONS = "quick_actions", "Quick Actions"
        CALENDAR = "calendar", "Calendar"

    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=50, choices=WidgetType.choices)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default="bi-grid")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order on dashboard")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Widget"
        verbose_name_plural = "Widgets"

    def __str__(self):
        return self.name


class UserWidget(models.Model):
    """User-specific widget configuration"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_widgets')
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE, related_name='user_configs')
    is_enabled = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['user', 'widget']
        verbose_name = "User Widget"
        verbose_name_plural = "User Widgets"

    def __str__(self):
        return f"{self.user.username} - {self.widget.name}"


class QuickAction(models.Model):
    """Quick actions that can be added to the dashboard"""
    class ActionType(models.TextChoices):
        LINK = "link", "External Link"
        PAGE = "page", "Internal Page"
        FUNCTION = "function", "JavaScript Function"

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    action_type = models.CharField(max_length=50, choices=ActionType.choices)
    url = models.URLField(blank=True, help_text="For link and page actions")
    icon = models.CharField(max_length=50, default="bi-lightning")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Quick Action"
        verbose_name_plural = "Quick Actions"

    def __str__(self):
        return self.name


class UserQuickAction(models.Model):
    """User-specific quick action configuration"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_quick_actions')
    quick_action = models.ForeignKey(QuickAction, on_delete=models.CASCADE, related_name='user_configs')
    is_enabled = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['user', 'quick_action']
        verbose_name = "User Quick Action"
        verbose_name_plural = "User Quick Actions"

    def __str__(self):
        return f"{self.user.username} - {self.quick_action.name}"
