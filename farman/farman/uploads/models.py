"""
Upload Models - File Management and Versioning
Supports daily updates, overwriting, and file history
"""
from django.db import models
from django.utils import timezone
import pandas as pd
from pathlib import Path
from farman.core.models import TimeStampedModel, SoftDeleteModel
from farman.companies.models import Company, Branch, Department


class UploadedFile(SoftDeleteModel):
    """
    Main model for uploaded Excel/CSV files
    Supports versioning and daily updates
    """
    DOMAIN_CHOICES = [
        ('unknown', 'نامشخص'),
        ('sales', 'فروش'),
        ('inventory', 'انبار'),
        ('accounting', 'حسابداری'),
        ('hr', 'منابع انسانی'),
        ('attendance', 'حضور و غیاب'),
        ('production', 'تولید'),
        ('purchasing', 'خرید'),
        ('crm', 'مشتریان'),
        ('banking', 'بانکی'),
        ('checks', 'چک‌ها'),
        ('payroll', 'حقوق و دستمزد'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار پردازش'),
        ('analyzing', 'در حال تحلیل'),
        ('cleaning', 'در حال پاکسازی'),
        ('validated', 'تأیید شده'),
        ('processed', 'پردازش شده'),
        ('failed', 'ناموفق'),
        ('rejected', 'رد شده'),
    ]
    
    # Basic Information
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name='شرکت'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files',
        verbose_name='شعبه'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files',
        verbose_name='بخش'
    )
    uploaded_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
        verbose_name='آپلود کننده'
    )
    
    # File Information
    original_filename = models.CharField('نام فایل اصلی', max_length=255)
    file = models.FileField('فایل', upload_to='uploads/%Y/%m/%d/')
    file_type = models.CharField('نوع فایل', max_length=10, choices=[
        ('xlsx', 'Excel (.xlsx)'),
        ('xls', 'Excel (.xls)'),
        ('csv', 'CSV (.csv)'),
    ])
    file_size = models.BigIntegerField('اندازه فایل (بایت)', default=0)
    
    # Domain Detection
    detected_domain = models.CharField(
        'دامنه تشخیص داده شده',
        max_length=30,
        choices=DOMAIN_CHOICES,
        default='unknown'
    )
    domain_confidence = models.DecimalField(
        'اطمینان تشخیص',
        max_digits=5,
        decimal_places=4,
        default=0.0,
        help_text='بین 0 تا 1'
    )
    requires_confirmation = models.BooleanField('نیاز به تأیید', default=True)
    user_confirmed_domain = models.CharField(
        'دامنه تأیید شده توسط کاربر',
        max_length=30,
        choices=DOMAIN_CHOICES,
        null=True,
        blank=True
    )
    
    # Processing Status
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_started_at = models.DateTimeField('شروع پردازش', null=True, blank=True)
    processing_completed_at = models.DateTimeField('پایان پردازش', null=True, blank=True)
    error_message = models.TextField('پیام خطا', blank=True)
    
    # Data Statistics
    total_rows = models.IntegerField('تعداد سطرها', default=0)
    total_columns = models.IntegerField('تعداد ستون‌ها', default=0)
    cleaned_rows = models.IntegerField('سطرهای پاکسازی شده', default=0)
    duplicate_rows_removed = models.IntegerField('سطرهای تکراری حذف شده', default=0)
    invalid_rows_removed = models.IntegerField('سطرهای نامعتبر حذف شده', default=0)
    
    # Versioning & Daily Updates
    is_latest_version = models.BooleanField('آخرین نسخه', default=True)
    version_number = models.PositiveIntegerField('شماره نسخه', default=1)
    parent_file = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versions',
        verbose_name='فایل والد'
    )
    date_key = models.DateField(
        'کلید تاریخی',
        null=True,
        blank=True,
        help_text='برای شناسایی فایل‌های روزانه جهت جایگزینی'
    )
    
    # AI Processing Results
    column_mappings = models.JSONField(
        'نگاشت ستون‌ها',
        default=dict,
        help_text='Mapping of original columns to standardized names'
    )
    data_quality_score = models.DecimalField(
        'امتیاز کیفیت داده',
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text='بین 0 تا 100'
    )
    anomalies_detected = models.JSONField(
        'ناهنجاری‌های تشخیص داده شده',
        default=list,
        blank=True
    )
    
    # Generated Files
    cleaned_file = models.FileField(
        'فایل پاکسازی شده',
        upload_to='uploads/cleaned/%Y/%m/%d/',
        blank=True,
        null=True
    )
    dashboard_file = models.FileField(
        'فایل داشبورد',
        upload_to='uploads/dashboards/%Y/%m/%d/',
        blank=True,
        null=True
    )
    
    # Metadata
    notes = models.TextField('یادداشت‌ها', blank=True)
    tags = models.JSONField('برچسب‌ها', default=list, blank=True)
    
    class Meta:
        verbose_name = 'فایل آپلود شده'
        verbose_name_plural = 'فایل‌های آپلود شده'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'detected_domain']),
            models.Index(fields=['date_key']),
            models.Index(fields=['is_latest_version']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.company.name})"
    
    @property
    def domain_display(self):
        """Get display name for domain"""
        return self.get_detected_domain_display()
    
    def get_all_versions(self):
        """Get all versions of this file including itself"""
        if self.parent_file:
            return self.parent_file.versions.all()
        return self.versions.all()
    
    def archive_current_version(self):
        """Archive current version before creating new one"""
        self.is_latest_version = False
        self.save(update_fields=['is_latest_version'])
    
    def can_overwrite(self):
        """Check if this file can be overwritten by a new daily update"""
        return self.is_latest_version and self.date_key is not None


class ColumnMapping(TimeStampedModel):
    """
    Stores mapping between original column names and standardized names
    Part of the Semantic Layer
    """
    uploaded_file = models.ForeignKey(
        UploadedFile,
        on_delete=models.CASCADE,
        related_name='column_mappings',
        verbose_name='فایل'
    )
    original_name = models.CharField('نام اصلی', max_length=255)
    standardized_name = models.CharField('نام استاندارد', max_length=255)
    data_type = models.CharField(
        'نوع داده',
        max_length=20,
        choices=[
            ('string', 'متن'),
            ('integer', 'عدد صحیح'),
            ('float', 'عدد اعشاری'),
            ('date', 'تاریخ'),
            ('datetime', 'تاریخ و زمان'),
            ('boolean', 'بولی'),
            ('currency', 'ارز'),
            ('percentage', 'درصد'),
        ]
    )
    semantic_category = models.CharField(
        'دسته معنایی',
        max_length=100,
        blank=True,
        help_text='e.g., customer_name, product_code, quantity, price'
    )
    is_primary_key = models.BooleanField('کلید اصلی', default=False)
    is_nullable = models.BooleanField('قابل خالی بودن', default=True)
    sample_values = models.JSONField('مقادیر نمونه', default=list)
    
    class Meta:
        verbose_name = 'نگاشت ستون'
        verbose_name_plural = 'نگاشت‌های ستون'
        unique_together = ['uploaded_file', 'original_name']
    
    def __str__(self):
        return f"{self.original_name} → {self.standardized_name}"


class DataRow(SoftDeleteModel):
    """
    Individual data rows stored in database
    Normalized and cleaned data from uploaded files
    """
    uploaded_file = models.ForeignKey(
        UploadedFile,
        on_delete=models.CASCADE,
        related_name='data_rows',
        verbose_name='فایل'
    )
    row_number = models.IntegerField('شماره سطر', db_index=True)
    data = models.JSONField('داده‌ها', default=dict)
    is_valid = models.BooleanField('معتبر', default=True)
    validation_errors = models.JSONField('خطاهای اعتبارسنجی', default=list, blank=True)
    
    class Meta:
        verbose_name = 'سطر داده'
        verbose_name_plural = 'سطرهای داده'
        ordering = ['row_number']
        indexes = [
            models.Index(fields=['uploaded_file', 'is_valid']),
        ]
    
    def __str__(self):
        return f"Row {self.row_number} - {self.uploaded_file.original_filename}"
