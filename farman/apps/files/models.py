"""
Farman File Management Models
Handles Excel uploads, versioning, domain detection, and processing status
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
import os


class UploadedFile(TimeStampedModel):
    """
    Represents an uploaded Excel file
    Supports versioning - new uploads with same name override previous versions
    """

    DOMAIN_CHOICES = [
        ('UNKNOWN', 'نامشخص'),
        ('INVENTORY', 'انبار'),
        ('SALES', 'فروش'),
        ('PURCHASING', 'خرید'),
        ('ACCOUNTING', 'حسابداری'),
        ('HR', 'منابع انسانی'),
        ('ATTENDANCE', 'حضور و غیاب'),
        ('PRODUCTION', 'تولید'),
        ('CRM', 'مشتریان'),
        ('FINANCE', 'امور مالی'),
        ('BANKING', 'بانکی'),
        ('CHECKS', 'چک‌ها'),
    ]

    STATUS_CHOICES = [
        ('UPLOADED', 'آپلود شده'),
        ('PROCESSING', 'در حال پردازش'),
        ('DETECTED', 'تشخیص داده شده'),
        ('CLEANING', 'در حال پاکسازی'),
        ('CLEANED', 'پاکسازی شده'),
        ('IMPORTED', 'وارد شده به دیتابیس'),
        ('ERROR', 'خطا'),
        ('REJECTED', 'رد شده'),
    ]

    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name=_('شرکت')
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files',
        verbose_name=_('دپارتمان')
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
        verbose_name=_('آپلود کننده')
    )

    # File info
    file = models.FileField(
        upload_to='uploads/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls', 'csv'])],
        verbose_name=_('فایل')
    )
    original_filename = models.CharField(max_length=255, verbose_name=_('نام فایل اصلی'))
    file_size = models.BigIntegerField(verbose_name=_('اندازه فایل (بایت)'))
    file_hash = models.CharField(max_length=64, db_index=True, verbose_name=_('هش فایل'))

    # Versioning
    file_name_key = models.CharField(
        max_length=255,
        verbose_name=_('کلید نام فایل برای ورژن‌بندی')
    )
    version = models.IntegerField(default=1, verbose_name=_('نسخه'))
    is_latest_version = models.BooleanField(default=True, verbose_name=_('آخرین نسخه'))
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='next_versions',
        verbose_name=_('نسخه قبلی')
    )

    # AI Detection
    detected_domain = models.CharField(
        max_length=50,
        choices=DOMAIN_CHOICES,
        default='UNKNOWN',
        verbose_name=_('دامنه تشخیص داده شده')
    )
    domain_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_('اطمینان تشخیص (٪)')
    )
    requires_confirmation = models.BooleanField(default=False, verbose_name=_('نیاز به تأیید'))
    ai_suggestions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('پیشنهادات هوش مصنوعی')
    )

    # Processing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='UPLOADED',
        verbose_name=_('وضعیت')
    )
    error_message = models.TextField(null=True, blank=True, verbose_name=_('پیام خطا'))
    processing_log = models.JSONField(default=list, blank=True, verbose_name=_('لاگ پردازش'))

    # Statistics
    row_count = models.IntegerField(default=0, verbose_name=_('تعداد سطر'))
    column_count = models.IntegerField(default=0, verbose_name=_('تعداد ستون'))
    duplicate_rows_removed = models.IntegerField(default=0, verbose_name=_('سطرهای تکراری حذف شده'))
    invalid_rows_removed = models.IntegerField(default=0, verbose_name=_('سطرهای نامعتبر حذف شده'))

    # Column mapping (Semantic Layer)
    column_mapping = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('نگاشت ستون‌ها به مفاهیم معنایی')
    )

    # Processing timestamps
    detected_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان تشخیص'))
    cleaned_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان پاکسازی'))
    imported_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان وارد کردن'))

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['file_name_key', '-version']),
            models.Index(fields=['detected_domain']),
            models.Index(fields=['file_hash']),
        ]
        verbose_name = _('فایل آپلود شده')
        verbose_name_plural = _('فایل‌های آپلود شده')

    def __str__(self):
        return f"{self.original_filename} (v{self.version}) - {self.company.name}"

    def save(self, *args, **kwargs):
        # Auto-generate file_name_key from original filename if not set
        if not self.file_name_key:
            base_name = os.path.splitext(self.original_filename)[0]
            # Normalize: lowercase, replace spaces with underscores
            self.file_name_key = base_name.lower().replace(' ', '_').replace('-', '_')

        # Auto-calculate file size
        if self.file and not self.file_size:
            self.file_size = self.file.size

        # Generate file hash for deduplication
        if self.file and not self.file_hash:
            import hashlib
            self.file.seek(0)
            file_content = self.file.read()
            self.file_hash = hashlib.sha256(file_content).hexdigest()
            self.file.seek(0)  # Reset file pointer

        super().save(*args, **kwargs)

    def get_file_url(self):
        """Get download URL for the file"""
        if self.file:
            return self.file.url
        return None

    def mark_as_error(self, error_message: str):
        """Mark file processing as failed"""
        self.status = 'ERROR'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def add_processing_log(self, message: str, level: str = 'INFO'):
        """Add entry to processing log"""
        from datetime import datetime
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        if not self.processing_log:
            self.processing_log = []
        self.processing_log.append(log_entry)
        self.save(update_fields=['processing_log'])


class FileProcessingTask(models.Model):
    """
    Tracks background processing tasks for files
    """

    TASK_TYPE_CHOICES = [
        ('DETECT_DOMAIN', 'تشخیص دامنه'),
        ('CLEAN_DATA', 'پاکسازی داده'),
        ('GENERATE_EXCEL', 'تولید اکسل حرفه‌ای'),
        ('IMPORT_TO_DB', 'وارد کردن به دیتابیس'),
        ('BUILD_KNOWLEDGE_GRAPH', 'ساخت گراف دانش'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'در انتظار'),
        ('RUNNING', 'در حال اجرا'),
        ('COMPLETED', 'تکمیل شده'),
        ('FAILED', 'ناموفق'),
        ('RETRY', 'در حال تلاش مجدد'),
    ]

    file = models.ForeignKey(
        UploadedFile,
        on_delete=models.CASCADE,
        related_name='processing_tasks',
        verbose_name=_('فایل')
    )
    task_type = models.CharField(
        max_length=50,
        choices=TASK_TYPE_CHOICES,
        verbose_name=_('نوع وظیفه')
    )
    celery_task_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_('شناسه تسک Celery')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name=_('وضعیت')
    )
    progress_percentage = models.IntegerField(default=0, verbose_name=_('درصد پیشرفت'))
    result_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('داده نتیجه')
    )
    error_message = models.TextField(null=True, blank=True, verbose_name=_('پیام خطا'))
    started_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان شروع'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('زمان تکمیل'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['celery_task_id']),
        ]
        verbose_name = _('وظیفه پردازش فایل')
        verbose_name_plural = _('وظایف پردازش فایل')

    def __str__(self):
        return f"{self.get_task_type_display()} - {self.file.original_filename} - {self.get_status_display()}"


class CleanedDataSnapshot(models.Model):
    """
    Stores cleaned data snapshots before importing to main tables
    This allows rollback and re-processing without re-uploading
    """

    file = models.ForeignKey(
        UploadedFile,
        on_delete=models.CASCADE,
        related_name='cleaned_snapshots',
        verbose_name=_('فایل')
    )
    snapshot_data = models.JSONField(verbose_name=_('داده پاکسازی شده'))
    schema = models.JSONField(verbose_name=_('اسکیمای داده'))
    row_count = models.IntegerField(verbose_name=_('تعداد سطر'))
    column_count = models.IntegerField(verbose_name=_('تعداد ستون'))
    checksum = models.CharField(max_length=64, verbose_name=_('چک‌سام داده'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['file', '-created_at']),
        ]
        verbose_name = _('اسنپ‌شات داده پاکسازی شده')
        verbose_name_plural = _('اسنپ‌شات‌های داده پاکسازی شده')

    def __str__(self):
        return f"Snapshot for {self.file.original_filename} - {self.row_count} rows"


# Abstract base model for domain-specific tables
class DomainDataBase(models.Model):
    """
    Abstract base model for all domain-specific data tables
    Provides common fields and multi-tenancy isolation
    """

    company = models.ForeignKey(
        'accounts.Company',
        on_delete=models.CASCADE,
        verbose_name=_('شرکت')
    )
    department = models.ForeignKey(
        'accounts.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('دپارتمان')
    )
    source_file = models.ForeignKey(
        UploadedFile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('فایل منبع')
    )
    row_hash = models.CharField(
        max_length=64,
        db_index=True,
        verbose_name=_('هش رکورد برای تشخیص تکراری')
    )
    is_active = models.BooleanField(default=True, verbose_name=_('فعال'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ ایجاد'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('تاریخ به‌روزرسانی'))
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_('تاریخ حذف'))

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['company', '-created_at']),
            models.Index(fields=['row_hash']),
        ]
