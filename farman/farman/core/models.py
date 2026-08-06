"""
Core Models - User, Company, and Base Models
Enterprise-grade multi-tenant architecture with Row-Level Security
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets
import string
from farman.settings import COMPANY_CODE_PREFIX, COMPANY_CODE_LENGTH, TRIAL_PERIOD_DAYS


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('ایمیل باید وارد شود')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Model with email as username
    Supports multi-company access with role-based permissions
    """
    username = None  # Remove username field
    email = models.EmailField('ایمیل', unique=True)
    phone_number = models.CharField('شماره تلفن', max_length=15, blank=True, null=True)
    first_name = models.CharField('نام', max_length=50)
    last_name = models.CharField('نام خانوادگی', max_length=50)
    avatar = models.ImageField('آواتار', upload_to='avatars/', blank=True, null=True)
    
    # Multi-company access
    companies = models.ManyToManyField(
        'companies.Company',
        through='companies.CompanyMembership',
        related_name='users',
        verbose_name='شرکت‌ها'
    )
    
    # Default company for quick access
    default_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_users',
        verbose_name='شرکت پیش‌فرض'
    )
    
    # Preferences
    language = models.CharField(
        'زبان',
        max_length=10,
        choices=[('fa', 'فارسی'), ('en', 'English')],
        default='fa'
    )
    theme = models.CharField(
        'تم',
        max_length=10,
        choices=[('light', 'روشن'), ('dark', 'تاریک')],
        default='light'
    )
    timezone = models.CharField('منطقه زمانی', max_length=50, default='Asia/Tehran')
    
    # Security
    two_factor_enabled = models.BooleanField('احراز هویت دو مرحله‌ای', default=False)
    two_factor_secret = models.CharField('رمز دو مرحله‌ای', max_length=32, blank=True, null=True)
    last_login_ip = models.GenericIPAddressField('آخرین IP ورود', null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField('تلاش‌های ناموفق', default=0)
    locked_until = models.DateTimeField('قفل تا', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def can_access_company(self, company):
        """Check if user has access to a specific company"""
        return self.companies.filter(id=company.id).exists()
    
    def get_role_in_company(self, company):
        """Get user's role in a specific company"""
        try:
            membership = self.companymembership_set.get(company=company)
            return membership.role
        except CompanyMembership.DoesNotExist:
            return None
    
    def is_locked(self):
        """Check if account is locked due to failed attempts"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=15)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])
    
    def reset_failed_logins(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])


class TimeStampedModel(models.Model):
    """
    Abstract base model with created_at and updated_at fields
    """
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)
    
    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Custom manager that excludes soft-deleted records"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(TimeStampedModel):
    """
    Abstract base model with soft delete functionality
    """
    deleted_at = models.DateTimeField('تاریخ حذف', null=True, blank=True, db_index=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False, soft=True):
        if soft:
            self.deleted_at = timezone.now()
            self.save(update_fields=['deleted_at'])
        else:
            super().delete(using=using, keep_parents=keep_parents)
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None


# Import CompanyMembership here to avoid circular imports
from farman.companies.models import CompanyMembership
