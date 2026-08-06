"""
Django Models for Security Module
Audit logging, rate limiting tracking, and security events
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """Comprehensive audit log for all system actions"""
    
    ACTION_TYPES = [
        ('LOGIN', 'ورود به سیستم'),
        ('LOGOUT', 'خروج از سیستم'),
        ('UPLOAD_FILE', 'آپلود فایل'),
        ('DOWNLOAD_FILE', 'دانلود فایل'),
        ('DELETE_DATA', 'حذف داده'),
        ('UPDATE_DATA', 'به‌روزرسانی داده'),
        ('CREATE_DATA', 'ایجاد داده'),
        ('EXPORT_REPORT', 'خروجی گزارش'),
        ('CHANGE_PERMISSION', 'تغییر دسترسی'),
        ('API_CALL', 'درخواست API'),
        ('FAILED_LOGIN', 'ورود ناموفق'),
        ('RATE_LIMIT_EXCEEDED', 'تجاوز از محدودیت نرخ'),
        ('SECURITY_ALERT', 'هشدار امنیتی'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('کاربر')
    )
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('شرکت')
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        verbose_name=_('نوع اقدام')
    )
    action_name = models.CharField(
        max_length=200,
        verbose_name=_('نام اقدام')
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('جزئیات')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('آدرس IP')
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('User Agent')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان')
    )
    is_suspicious = models.BooleanField(
        default=False,
        verbose_name=_('مشکوک')
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['company', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['is_suspicious', '-timestamp']),
        ]
        verbose_name = _('لاگ حسابرسی')
        verbose_name_plural = _('لاگ‌های حسابرسی')
    
    def __str__(self):
        return f"{self.action_name} - {self.user} - {self.timestamp}"


class SecurityEvent(models.Model):
    """Security events and alerts"""
    
    SEVERITY_LEVELS = [
        ('LOW', 'کم'),
        ('MEDIUM', 'متوسط'),
        ('HIGH', 'بالا'),
        ('CRITICAL', 'بحرانی'),
    ]
    
    EVENT_TYPES = [
        ('BRUTE_FORCE', 'حملات بروت فورس'),
        ('SQL_INJECTION', 'تزریق SQL'),
        ('XSS_ATTEMPT', 'تلاش XSS'),
        ('CSRF_VIOLATION', 'نقض CSRF'),
        ('UNAUTHORIZED_ACCESS', 'دسترسی غیرمجاز'),
        ('DATA_BREACH', 'نشت داده'),
        ('SUSPICIOUS_ACTIVITY', 'فعالیت مشکوک'),
        ('RATE_LIMIT_EXCEEDED', 'تجاوز از محدودیت نرخ'),
    ]
    
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='security_events',
        verbose_name=_('شرکت')
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        verbose_name=_('نوع رویداد')
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='MEDIUM',
        verbose_name=_('سطح شدت')
    )
    description = models.TextField(
        verbose_name=_('توضیحات')
    )
    source_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('آدرس IP منبع')
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('User Agent')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('فراداده')
    )
    is_resolved = models.BooleanField(
        default=False,
        verbose_name=_('حل شده')
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('زمان حل')
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events',
        verbose_name=_('حل شده توسط')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان ایجاد')
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
            models.Index(fields=['is_resolved', '-created_at']),
        ]
        verbose_name = _('رویداد امنیتی')
        verbose_name_plural = _('رویدادهای امنیتی')
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.get_severity_display()} - {self.created_at}"


class RateLimitLog(models.Model):
    """Rate limiting logs"""
    
    endpoint = models.CharField(
        max_length=200,
        verbose_name=_('endpoint')
    )
    identifier = models.CharField(
        max_length=100,
        verbose_name=_('شناسه')
    )
    attempts = models.IntegerField(
        default=0,
        verbose_name=_('تعداد تلاش‌ها')
    )
    limit = models.IntegerField(
        verbose_name=_('محدودیت')
    )
    window_start = models.DateTimeField(
        verbose_name=_('شروع پنجره')
    )
    window_end = models.DateTimeField(
        verbose_name=_('پایان پنجره')
    )
    is_blocked = models.BooleanField(
        default=False,
        verbose_name=_('مسدود شده')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان ایجاد')
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['endpoint', 'identifier', '-created_at']),
            models.Index(fields=['is_blocked', '-created_at']),
        ]
        verbose_name = _('لاگ محدودیت نرخ')
        verbose_name_plural = _('لاگ‌های محدودیت نرخ')
    
    def __str__(self):
        return f"{self.endpoint} - {self.identifier} - {self.attempts}/{self.limit}"


class DataAccessLog(models.Model):
    """Data access logging for compliance"""
    
    ACCESS_TYPES = [
        ('READ', 'خواندن'),
        ('WRITE', 'نوشتن'),
        ('DELETE', 'حذف'),
        ('EXPORT', 'خروجی'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='data_access_logs',
        verbose_name=_('کاربر')
    )
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='data_access_logs',
        verbose_name=_('شرکت')
    )
    table_name = models.CharField(
        max_length=100,
        verbose_name=_('نام جدول')
    )
    record_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('شناسه رکورد')
    )
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPES,
        verbose_name=_('نوع دسترسی')
    )
    fields_accessed = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('فیلدهای دسترسی یافته')
    )
    query_snippet = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('بخشی از کوئری')
    )
    rows_affected = models.IntegerField(
        default=0,
        verbose_name=_('تعداد سطرهای تأثیر گرفته')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('زمان')
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['company', '-timestamp']),
            models.Index(fields=['table_name', '-timestamp']),
        ]
        verbose_name = _('لاگ دسترسی به داده')
        verbose_name_plural = _('لاگ‌های دسترسی به داده')
    
    def __str__(self):
        return f"{self.table_name} - {self.access_type} - {self.user} - {self.timestamp}"
