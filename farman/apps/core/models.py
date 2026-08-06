"""
Farman Core Models
Base models and domain entities for the entire platform
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid


class TimeStampedModel(models.Model):
    """Abstract base model with timestamps"""

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted records"""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class SoftDeleteModel(TimeStampedModel):
    """Abstract base model with soft delete capability"""

    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاریخ حذف'))
    is_deleted = models.BooleanField(default=False, verbose_name=_('حذف شده'))

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Include deleted records

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, soft=True):
        """Soft delete by default"""
        if soft:
            from django.utils import timezone
            self.deleted_at = timezone.now()
            self.is_deleted = True
            self.save(update_fields=['deleted_at', 'is_deleted'])
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted record"""
        self.deleted_at = None
        self.is_deleted = False
        self.save(update_fields=['deleted_at', 'is_deleted'])


class CompanyHealthScore(models.Model):
    """
    Daily company health score calculation
    Score range: 0-100
    """

    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='health_scores',
        verbose_name=_('شرکت')
    )
    score = models.IntegerField(verbose_name=_('امتیاز سلامت'))
    previous_score = models.IntegerField(null=True, blank=True, verbose_name=_('امتیاز قبلی'))
    score_change = models.IntegerField(default=0, verbose_name=_('تغییر امتیاز'))

    # Component scores (0-100 each)
    sales_score = models.IntegerField(default=0, verbose_name=_('امتیاز فروش'))
    liquidity_score = models.IntegerField(default=0, verbose_name=_('امتیاز نقدینگی'))
    inventory_score = models.IntegerField(default=0, verbose_name=_('امتیاز موجودی'))
    receivables_score = models.IntegerField(default=0, verbose_name=_('امتیاز مطالبات'))
    attendance_score = models.IntegerField(default=0, verbose_name=_('امتیاز حضور و غیاب'))
    checks_score = models.IntegerField(default=0, verbose_name=_('امتیاز چک‌ها'))
    payments_score = models.IntegerField(default=0, verbose_name=_('امتیاز پرداخت‌ها'))
    profit_score = models.IntegerField(default=0, verbose_name=_('امتیاز سود'))

    # Key metrics snapshot
    total_sales = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name=_('فروش کل (تومان)'))
    total_purchases = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name=_('خرید کل (تومان)'))
    cash_balance = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name=_('موجودی نقد (تومان)'))
    critical_items_count = models.IntegerField(default=0, verbose_name=_('تعداد کالاهای بحرانی'))
    absent_employees_count = models.IntegerField(default=0, verbose_name=_('تعداد کارکنان غایب'))
    upcoming_checks_count = models.IntegerField(default=0, verbose_name=_('تعداد چک‌های سررسید شده'))
    unpaid_salaries_count = models.IntegerField(default=0, verbose_name=_('تعداد حقوق‌های پرداخت نشده'))

    # Insights
    positive_factors = models.JSONField(default=list, verbose_name=_('عوامل مثبت'))
    negative_factors = models.JSONField(default=list, verbose_name=_('عوامل منفی'))
    recommendations = models.JSONField(default=list, verbose_name=_('پیشنهادات'))

    date = models.DateField(verbose_name=_('تاریخ'))
    calculated_at = models.DateTimeField(auto_now_add=True, verbose_name=_('زمان محاسبه'))

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['company', '-date']),
            models.Index(fields=['-score']),
        ]
        verbose_name = _('امتیاز سلامت شرکت')
        verbose_name_plural = _('امتیازهای سلامت شرکت')
        unique_together = [['company', 'date']]

    def __str__(self):
        return f"{self.company.name} - {self.score}/100 - {self.date}"

    def save(self, *args, **kwargs):
        # Calculate score change
        if self.previous_score:
            self.score_change = self.score - self.previous_score
        super().save(*args, **kwargs)


class SystemSetting(TimeStampedModel):
    """System-wide settings"""

    SETTING_TYPES = [
        ('STRING', 'متن'),
        ('INTEGER', 'عدد صحیح'),
        ('DECIMAL', 'عدد اعشاری'),
        ('BOOLEAN', 'بولی'),
        ('JSON', 'جیسون'),
    ]

    key = models.CharField(max_length=100, unique=True, verbose_name=_('کلید'))
    value = models.TextField(verbose_name=_('مقدار'))
    setting_type = models.CharField(
        max_length=20,
        choices=SETTING_TYPES,
        default='STRING',
        verbose_name=_('نوع تنظیم')
    )
    description = models.TextField(null=True, blank=True, verbose_name=_('توضیحات'))
    is_public = models.BooleanField(default=False, verbose_name=_('عمومی'))
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='settings',
        verbose_name=_('شرکت')
    )

    class Meta:
        ordering = ['key']
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['company', 'key']),
        ]
        verbose_name = _('تنظیم سیستم')
        verbose_name_plural = _('تنظیمات سیستم')

    def __str__(self):
        return f"{self.key} = {self.value[:50]}..."


class Notification(models.Model):
    """System notifications for users"""

    PRIORITY_CHOICES = [
        ('LOW', 'کم'),
        ('NORMAL', 'عادی'),
        ('HIGH', 'بالا'),
        ('URGENT', 'فوری'),
    ]

    TYPE_CHOICES = [
        ('INFO', 'اطلاعات'),
        ('WARNING', 'هشدار'),
        ('ERROR', 'خطا'),
        ('SUCCESS', 'موفقیت'),
        ('DAILY_BRIEF', 'گزارش روزانه'),
        ('SECURITY_ALERT', 'هشدار امنیتی'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('کاربر')
    )
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('شرکت')
    )
    title = models.CharField(max_length=200, verbose_name=_('عنوان'))
    message = models.TextField(verbose_name=_('پیام'))
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='INFO',
        verbose_name=_('نوع')
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='NORMAL',
        verbose_name=_('اولویت')
    )
    data = models.JSONField(default=dict, blank=True, verbose_name=_('داده‌های اضافی'))
    is_read = models.BooleanField(default=False, verbose_name=_('خوانده شده'))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان خواندن'))
    action_url = models.URLField(null=True, blank=True, verbose_name=_('لینک اقدام'))
    action_text = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('متن اقدام'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['company', '-created_at']),
        ]
        verbose_name = _('اعلان')
        verbose_name_plural = _('اعلان‌ها')

    def __str__(self):
        return f"{self.title} - {self.user}"

    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])


class ActivityLog(models.Model):
    """User activity tracking within companies"""

    ACTION_CHOICES = [
        ('LOGIN', 'ورود'),
        ('LOGOUT', 'خروج'),
        ('UPLOAD_FILE', 'آپلود فایل'),
        ('DOWNLOAD_FILE', 'دانلود فایل'),
        ('CREATE_RECORD', 'ایجاد رکورد'),
        ('UPDATE_RECORD', 'به‌روزرسانی رکورد'),
        ('DELETE_RECORD', 'حذف رکورد'),
        ('EXPORT_DATA', 'خروجی داده'),
        ('VIEW_REPORT', 'مشاهده گزارش'),
        ('ASK_AI', 'سؤال از هوش مصنوعی'),
        ('CHANGE_SETTINGS', 'تغییر تنظیمات'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
        verbose_name=_('کاربر')
    )
    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name=_('شرکت')
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name=_('دپارتمان')
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        verbose_name=_('اقدام')
    )
    description = models.TextField(null=True, blank=True, verbose_name=_('توضیحات'))
    entity_type = models.CharField(max_length=100, null=True, blank=True, verbose_name=_('نوع موجودیت'))
    entity_id = models.BigIntegerField(null=True, blank=True, verbose_name=_('شناسه موجودیت'))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('فراداده'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('آدرس IP'))
    user_agent = models.TextField(null=True, blank=True, verbose_name=_('User Agent'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]
        verbose_name = _('لاگ فعالیت')
        verbose_name_plural = _('لاگ‌های فعالیت')

    def __str__(self):
        return f"{self.get_action_display()} - {self.user} - {self.created_at}"
