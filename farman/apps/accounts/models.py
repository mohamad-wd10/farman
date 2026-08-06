"""
Accounts Module Models for Farman Platform
Handles companies, users, departments, roles, and subscriptions
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import secrets
from datetime import datetime, timedelta


class Company(models.Model):
    """Company model for multi-tenancy"""
    
    STATUS_CHOICES = [
        ('TRIAL', 'دوره آزمایشی'),
        ('ACTIVE', 'فعال'),
        ('SUSPENDED', 'معلق'),
        ('CANCELLED', 'لغو شده'),
    ]
    
    INDUSTRY_CHOICES = [
        ('MANUFACTURING', 'تولیدی'),
        ('TRADING', 'بازرگانی'),
        ('SERVICES', 'خدماتی'),
        ('TECHNOLOGY', 'فناوری'),
        ('FINANCE', 'مالی'),
        ('HEALTHCARE', 'درمانی'),
        ('EDUCATION', 'آموزشی'),
        ('OTHER', 'سایر'),
    ]
    
    name = models.CharField(max_length=200, verbose_name=_('نام شرکت'))
    code = models.CharField(max_length=20, unique=True, verbose_name=_('کد اختصاصی شرکت'))
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        default='OTHER',
        verbose_name=_('صنعت')
    )
    employee_count = models.IntegerField(null=True, blank=True, verbose_name=_('تعداد کارکنان'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='TRIAL',
        verbose_name=_('وضعیت')
    )
    trial_start_date = models.DateTimeField(null=True, blank=True, verbose_name=_('شروع دوره آزمایشی'))
    trial_end_date = models.DateTimeField(null=True, blank=True, verbose_name=_('پایان دوره آزمایشی'))
    subscription_start_date = models.DateTimeField(null=True, blank=True, verbose_name=_('شروع اشتراک'))
    subscription_end_date = models.DateTimeField(null=True, blank=True, verbose_name=_('پایان اشتراک'))
    logo = models.ImageField(upload_to='companies/logos/', null=True, blank=True, verbose_name=_('لوگو'))
    address = models.TextField(null=True, blank=True, verbose_name=_('آدرس'))
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('تلفن'))
    email = models.EmailField(null=True, blank=True, verbose_name=_('ایمیل'))
    website = models.URLField(null=True, blank=True, verbose_name=_('وب‌سایت'))
    tax_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('شناسه مالیاتی'))
    registration_number = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('شماره ثبت'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = _('شرکت')
        verbose_name_plural = _('شرکت‌ها')
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def save(self, *args, **kwargs):
        if not self.code:
            from apps.security.core import SecurityConfig
            self.code = SecurityConfig.generate_company_code(self.name)
        
        if not self.trial_start_date:
            self.trial_start_date = datetime.now()
            self.trial_end_date = self.trial_start_date + timedelta(days=14)
        
        super().save(*args, **kwargs)
    
    def is_trial_active(self):
        """Check if trial period is still active"""
        if self.status == 'TRIAL' and self.trial_end_date:
            return datetime.now() < self.trial_end_date
        return False
    
    def is_subscription_active(self):
        """Check if subscription is still active"""
        if self.status == 'ACTIVE' and self.subscription_end_date:
            return datetime.now() < self.subscription_end_date
        return False
    
    def can_access_platform(self):
        """Check if company can access the platform"""
        return self.is_trial_active() or self.is_subscription_active()


class User(AbstractUser):
    """Custom user model with company relation"""
    
    ROLE_CHOICES = [
        ('OWNER', 'مالک'),
        ('ADMIN', 'مدیر'),
        ('MANAGER', 'مدیر بخش'),
        ('USER', 'کاربر'),
        ('VIEWER', 'مشاهده‌گر'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        verbose_name=_('شرکت')
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='USER',
        verbose_name=_('نقش')
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('دپارتمان')
    )
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name=_('تلفن همراه'))
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True, verbose_name=_('تصویر پروفایل'))
    is_verified = models.BooleanField(default=False, verbose_name=_('تأیید شده'))
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('آخرین IP ورود'))
    password_changed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاریخ تغییر رمز'))
    must_change_password = models.BooleanField(default=True, verbose_name=_('اجبار به تغییر رمز'))
    
    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['company', '-date_joined']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
        ]
        verbose_name = _('کاربر')
        verbose_name_plural = _('کاربران')
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.company.name if self.company else 'بدون شرکت'})"
    
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if self.is_superuser:
            return True
        
        # Role-based permissions
        role_permissions = {
            'OWNER': ['all'],
            'ADMIN': ['manage_users', 'manage_departments', 'view_reports', 'upload_files', 'delete_data'],
            'MANAGER': ['view_reports', 'upload_files', 'manage_department'],
            'USER': ['view_reports', 'upload_files'],
            'VIEWER': ['view_reports'],
        }
        
        user_perms = role_permissions.get(self.role, [])
        return permission in user_perms or 'all' in user_perms


class Department(models.Model):
    """Department model for organizational structure"""
    
    DEPARTMENT_TYPES = [
        ('WAREHOUSE', 'انبار'),
        ('SALES', 'فروش'),
        ('ACCOUNTING', 'حسابداری'),
        ('HR', 'منابع انسانی'),
        ('PRODUCTION', 'تولید'),
        ('PURCHASING', 'خرید'),
        ('CRM', 'مشتریان'),
        ('FINANCE', 'امور مالی'),
        ('IT', 'فناوری اطلاعات'),
        ('OTHER', 'سایر'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_('شرکت')
    )
    name = models.CharField(max_length=100, verbose_name=_('نام دپارتمان'))
    department_type = models.CharField(
        max_length=50,
        choices=DEPARTMENT_TYPES,
        default='OTHER',
        verbose_name=_('نوع دپارتمان')
    )
    description = models.TextField(null=True, blank=True, verbose_name=_('توضیحات'))
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('مدیر دپارتمان')
    )
    parent_department = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_departments',
        verbose_name=_('دپارتمان والد')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'department_type']),
            models.Index(fields=['parent_department']),
        ]
        verbose_name = _('دپارتمان')
        verbose_name_plural = _('دپارتمان‌ها')
        unique_together = [['company', 'name']]
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"


class SubscriptionPlan(models.Model):
    """Subscription plans for companies"""
    
    PLAN_TYPES = [
        ('TRIAL', 'آزمایشی (۱۴ روزه)'),
        ('MONTHLY', 'ماهانه'),
        ('YEARLY', 'سالانه'),
        ('ENTERPRISE', 'سازمانی'),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_('نام پلن'))
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        unique=True,
        verbose_name=_('نوع پلن')
    )
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('قیمت (دلار)'))
    price_irt = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name=_('قیمت (تومان)'))
    duration_days = models.IntegerField(default=30, verbose_name=_('مدت (روز)'))
    max_users = models.IntegerField(null=True, blank=True, verbose_name=_('حداکثر کاربر'))
    max_departments = models.IntegerField(null=True, blank=True, verbose_name=_('حداکثر دپارتمان'))
    max_storage_gb = models.IntegerField(default=10, verbose_name=_('حداکثر فضای ذخیره‌سازی (GB)'))
    features = models.JSONField(default=list, verbose_name=_('ویژگی‌ها'))
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    
    class Meta:
        ordering = ['price_usd']
        verbose_name = _('پلن اشتراک')
        verbose_name_plural = ('پلن‌های اشتراک')
    
    def __str__(self):
        return f"{self.name} - ${self.price_usd}"


class PaymentRequest(models.Model):
    """Payment requests from companies"""
    
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار بررسی'),
        ('APPROVED', 'تأیید شده'),
        ('REJECTED', 'رد شده'),
        ('COMPLETED', 'تکمیل شده'),
    ]
    
    PAYMENT_METHODS = [
        ('BANK_TRANSFER', 'واریز بانکی'),
        ('CHECK', 'چک'),
        ('CRYPTO', 'ارز دیجیتال'),
        ('OTHER', 'سایر'),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='payment_requests',
        verbose_name=_('شرکت')
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='payment_requests',
        verbose_name=_('پلن')
    )
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name=_('مبلغ (تومان)'))
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='BANK_TRANSFER',
        verbose_name=_('روش پرداخت')
    )
    payment_proof = models.ImageField(
        upload_to='payments/proofs/',
        null=True,
        blank=True,
        verbose_name=_('تصویر فیش واریزی')
    )
    description = models.TextField(null=True, blank=True, verbose_name=_('توضیحات'))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name=_('وضعیت')
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_payments',
        verbose_name=_('بررسی شده توسط')
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان بررسی'))
    rejection_reason = models.TextField(null=True, blank=True, verbose_name=_('علت رد'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ درخواست'))
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]
        verbose_name = _('درخواست پرداخت')
        verbose_name_plural = _('درخواست‌های پرداخت')
    
    def __str__(self):
        return f"{self.company.name} - {self.plan.name} - {self.get_status_display()}"
