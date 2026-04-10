from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
import uuid

User = get_user_model()


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
        max_length=10,
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
    
    class Meta:
        ordering = ['-years_of_experience', 'skill_name']
        verbose_name = "Employee Skill"
        verbose_name_plural = "Employee Skills"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.skill_name}"


class EmployeeEducation(models.Model):
    """Employee education history"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-end_date']
        verbose_name = "Employee Education"
        verbose_name_plural = "Employee Education"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.degree} in {self.field_of_study}"


class EmployeeExperience(models.Model):
    """Employee work experience"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experience')
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-end_date', '-start_date']
        verbose_name = "Employee Experience"
        verbose_name_plural = "Employee Experience"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.position} at {self.company}"


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
    file = models.FileField(upload_to='employee_documents/%Y/%m/')
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
            return self.expiry_date < timezone.now().date()
        return False


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


class EmployeePerformance(models.Model):
    """Employee performance records"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_records')
    review_period = models.CharField(max_length=50)  # e.g., "Q1 2024", "Annual 2024"
    review_date = models.DateField()
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews_conducted')
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2)  # e.g., 4.5 out of 5
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    goals = models.TextField(blank=True)
    comments = models.TextField(blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-review_date']
        verbose_name = "Employee Performance"
        verbose_name_plural = "Employee Performance Records"
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.review_period}"
