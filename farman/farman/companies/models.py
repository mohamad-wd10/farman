"""
Company Models - Multi-tenant Architecture
Supports branches, departments, and hierarchical organization
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
import string
from farman.settings import COMPANY_CODE_PREFIX, COMPANY_CODE_LENGTH, TRIAL_PERIOD_DAYS
from farman.core.models import TimeStampedModel, SoftDeleteModel


def generate_company_code():
    """Generate unique company code"""
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(COMPANY_CODE_LENGTH - len(COMPANY_CODE_PREFIX)))
    return f"{COMPANY_CODE_PREFIX}-{random_part}"


class Company(SoftDeleteModel):
    """
    Company/Organization Model
    Each company has a unique code for branch identification
    """
    # Basic Information
    name = models.CharField('نام شرکت', max_length=200)
    code = models.CharField('کد اختصاصی', max_length=20, unique=True, default=generate_company_code)
    description = models.TextField('توضیحات', blank=True)
    
    # Business Details
    business_type = models.CharField(
        'نوع کسب‌وکار',
        max_length=50,
        choices=[
            ('trading', 'بازرگانی'),
            ('manufacturing', 'تولیدی'),
            ('services', 'خدماتی'),
            ('retail', 'فروشگاهی'),
            ('startup', 'استارتاپ'),
            ('other', 'سایر'),
        ],
        default='trading'
    )
    employee_count = models.IntegerField('تعداد کارکنان', default=1)
    industry = models.CharField('صنعت', max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField('ایمیل رسمی')
    phone = models.CharField('تلفن', max_length=20, blank=True)
    address = models.TextField('آدرس', blank=True)
    website = models.URLField('وب‌سایت', blank=True)
    logo = models.ImageField('لوگو', upload_to='companies/logos/', blank=True, null=True)
    
    # Subscription & Billing
    subscription_plan = models.CharField(
        'طرح اشتراک',
        max_length=20,
        choices=[
            ('trial', 'آزمایشی'),
            ('monthly', 'ماهانه'),
            ('yearly', 'سالانه'),
            ('enterprise', 'سازمانی'),
        ],
        default='trial'
    )
    trial_started_at = models.DateTimeField('شروع دوره آزمایشی', null=True, blank=True)
    trial_ends_at = models.DateTimeField('پایان دوره آزمایشی', null=True, blank=True)
    subscription_started_at = models.DateTimeField('شروع اشتراک', null=True, blank=True)
    subscription_ends_at = models.DateTimeField('پایان اشتراک', null=True, blank=True)
    is_active = models.BooleanField('فعال', default=True)
    
    # Features & Limits
    max_users = models.PositiveIntegerField('حداکثر کاربران', default=5)
    max_storage_gb = models.PositiveIntegerField('حداکثر فضای ذخیره‌سازی (GB)', default=10)
    ai_queries_per_month = models.PositiveIntegerField('تعداد پرسش‌های هوش مصنوعی در ماه', default=1000)
    ai_queries_used = models.PositiveIntegerField('پرسش‌های استفاده شده', default=0)
    
    # Settings
    currency = models.CharField('واحد پول', max_length=10, default='IRR')
    fiscal_year_start = models.DateField('شروع سال مالی', default=lambda: timezone.now().replace(month=1, day=1))
    timezone = models.CharField('منطقه زمانی', max_length=50, default='Asia/Tehran')
    language = models.CharField('زبان پیش‌فرض', max_length=10, default='fa')
    
    # AI & Analytics
    health_score = models.DecimalField(
        'امتیاز سلامت شرکت',
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='امتیاز بین 0 تا 100'
    )
    health_score_updated_at = models.DateTimeField('آخرین به‌روزرسانی امتیاز', null=True, blank=True)
    
    # Timestamps are inherited from SoftDeleteModel
    
    class Meta:
        verbose_name = 'شرکت'
        verbose_name_plural = 'شرکت‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        # Set trial period for new companies
        if not self.pk and self.subscription_plan == 'trial':
            now = timezone.now()
            self.trial_started_at = now
            self.trial_ends_at = now + timedelta(days=TRIAL_PERIOD_DAYS)
        
        # Update health score timestamp
        if self.health_score != 0:
            self.health_score_updated_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_trial_expired(self):
        """Check if trial period has expired"""
        if self.subscription_plan != 'trial':
            return False
        return timezone.now() > (self.trial_ends_at or timezone.now())
    
    @property
    def is_subscription_active(self):
        """Check if subscription is currently active"""
        if self.subscription_plan == 'trial':
            return not self.is_trial_expired
        if self.subscription_ends_at:
            return timezone.now() < self.subscription_ends_at
        return self.is_active
    
    @property
    def days_remaining(self):
        """Get remaining days in current plan"""
        if self.subscription_plan == 'trial':
            end_date = self.trial_ends_at
        else:
            end_date = self.subscription_ends_at
        
        if not end_date:
            return None
        
        delta = end_date - timezone.now()
        return max(0, delta.days)
    
    def can_add_user(self):
        """Check if company can add more users"""
        return self.users.count() < self.max_users
    
    def get_storage_used(self):
        """Calculate storage used by company in GB"""
        total_size = sum(
            file.file.size 
            for file in self.uploaded_files.all() 
            if file.file
        )
        return total_size / (1024 ** 3)  # Convert to GB
    
    def can_upload_file(self, file_size):
        """Check if company has enough storage for new file"""
        used = self.get_storage_used()
        new_file_gb = file_size / (1024 ** 3)
        return (used + new_file_gb) <= self.max_storage_gb


class CompanyMembership(TimeStampedModel):
    """
    Many-to-Many relationship between User and Company with roles
    """
    ROLE_CHOICES = [
        ('owner', 'مالک'),
        ('admin', 'مدیر'),
        ('manager', 'مدیر بخش'),
        ('employee', 'کارمند'),
        ('viewer', 'بازبین'),
    ]
    
    DEPARTMENT_CHOICES = [
        ('management', 'مدیریت'),
        ('sales', 'فروش'),
        ('inventory', 'انبار'),
        ('accounting', 'حسابداری'),
        ('hr', 'منابع انسانی'),
        ('production', 'تولید'),
        ('purchasing', 'خرید'),
        ('crm', 'مشتریان'),
        ('it', 'فناوری اطلاعات'),
        ('other', 'سایر'),
    ]
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='company_memberships')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField('نقش', max_length=20, choices=ROLE_CHOICES, default='employee')
    department = models.CharField(
        'بخش',
        max_length=30,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True
    )
    is_admin = models.BooleanField('دسترسی مدیر', default=False)
    joined_at = models.DateTimeField('تاریخ عضویت', auto_now_add=True)
    invited_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='invitations_sent'
    )
    invitation_accepted = models.BooleanField('پذیرش دعوت', default=True)
    
    class Meta:
        verbose_name = 'عضویت شرکت'
        verbose_name_plural = 'عضویت‌های شرکت'
        unique_together = ['user', 'company']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name} ({self.get_role_display()})"
    
    @property
    def permissions(self):
        """Get permissions based on role"""
        role_permissions = {
            'owner': ['all'],
            'admin': ['read', 'write', 'delete', 'manage_users', 'settings'],
            'manager': ['read', 'write', 'manage_department'],
            'employee': ['read', 'write'],
            'viewer': ['read'],
        }
        return role_permissions.get(self.role, [])


class Branch(SoftDeleteModel):
    """
    Branch/Shaba Model for multi-location companies
    All branches connect to the main company
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name='شرکت'
    )
    name = models.CharField('نام شعبه', max_length=200)
    code = models.CharField('کد شعبه', max_length=50, unique=True)
    address = models.TextField('آدرس', blank=True)
    phone = models.CharField('تلفن', max_length=20, blank=True)
    manager = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_branches',
        verbose_name='مدیر شعبه'
    )
    is_active = models.BooleanField('فعال', default=True)
    
    class Meta:
        verbose_name = 'شعبه'
        verbose_name_plural = 'شعب'
        unique_together = ['company', 'code']
        ordering = ['company', 'name']
    
    def __str__(self):
        return f"{self.company.name} - شعبه {self.name}"


class Department(SoftDeleteModel):
    """
    Department Model for organizational structure
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='شرکت'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='departments',
        verbose_name='شعبه'
    )
    name = models.CharField('نام بخش', max_length=200)
    code = models.CharField('کد بخش', max_length=50)
    description = models.TextField('توضیحات', blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='بخش والد'
    )
    manager = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name='مدیر بخش'
    )
    is_active = models.BooleanField('فعال', default=True)
    
    class Meta:
        verbose_name = 'بخش'
        verbose_name_plural = 'بخش‌ها'
        unique_together = ['company', 'code']
        ordering = ['company', 'parent', 'name']
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"
