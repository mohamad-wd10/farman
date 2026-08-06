"""
Django Admin Configuration for Security Module
Provides admin interface for audit logs, security events, and rate limiting
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from .models import AuditLog, SecurityEvent, RateLimitLog, DataAccessLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for audit logs"""
    
    list_display = ('action_name', 'user_link', 'company_link', 'action_type', 'ip_address', 'timestamp', 'is_suspicious_badge')
    list_filter = ('action_type', 'is_suspicious', 'timestamp', 'company')
    search_fields = ('user__username', 'user__email', 'action_name', 'ip_address', 'details')
    readonly_fields = ('user', 'company', 'action_type', 'action_name', 'details', 'ip_address', 'user_agent', 'timestamp', 'is_suspicious')
    date_hierarchy = 'timestamp'
    list_per_page = 50
    
    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="?q={}">{}</a>', obj.user.username, obj.user)
        return 'سیستم'
    user_link.short_description = 'کاربر'
    
    def company_link(self, obj):
        if obj.company:
            return format_html('<a href="?company_id={}">{}</a>', obj.company.id, obj.company.name)
        return '-'
    company_link.short_description = 'شرکت'
    
    def is_suspicious_badge(self, obj):
        if obj.is_suspicious:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ مشکوک</span>')
        return '<span style="color: green;">✓ عادی</span>'
    is_suspicious_badge.short_description = 'وضعیت'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion only for superusers
        return request.user.is_superuser


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Admin interface for security events"""
    
    list_display = ('event_type_badge', 'company_link', 'severity_badge', 'description_short', 'source_ip', 'is_resolved_badge', 'created_at')
    list_filter = ('event_type', 'severity', 'is_resolved', 'created_at', 'company')
    search_fields = ('description', 'source_ip', 'company__name')
    readonly_fields = ('company', 'event_type', 'severity', 'description', 'source_ip', 'user_agent', 'metadata', 'created_at', 'is_resolved', 'resolved_at', 'resolved_by')
    date_hierarchy = 'created_at'
    list_per_page = 50
    actions = ['mark_as_resolved']
    
    def event_type_badge(self, obj):
        colors = {
            'BRUTE_FORCE': 'red',
            'SQL_INJECTION': 'darkred',
            'XSS_ATTEMPT': 'orange',
            'CSRF_VIOLATION': 'purple',
            'UNAUTHORIZED_ACCESS': 'red',
            'DATA_BREACH': 'darkred',
            'SUSPICIOUS_ACTIVITY': 'orange',
            'RATE_LIMIT_EXCEEDED': 'blue',
        }
        color = colors.get(obj.event_type, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_event_type_display())
    event_type_badge.short_description = 'نوع رویداد'
    
    def severity_badge(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred',
        }
        color = colors.get(obj.severity, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_severity_display())
    severity_badge.short_description = 'شدت'
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'توضیحات'
    
    def company_link(self, obj):
        return format_html('<a href="?company_id={}">{}</a>', obj.company.id, obj.company.name)
    company_link.short_description = 'شرکت'
    
    def is_resolved_badge(self, obj):
        if obj.is_resolved:
            return '<span style="color: green;">✓ حل شده</span>'
        return '<span style="color: orange;">⏳ در انتظار</span>'
    is_resolved_badge.short_description = 'وضعیت'
    
    @admin.action(description='علامت‌گذاری به عنوان حل شده')
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True, resolved_at=now(), resolved_by=request.user)
        self.message_user(request, f'{updated} رویداد به عنوان حل شده علامت‌گذاری شد.')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(RateLimitLog)
class RateLimitLogAdmin(admin.ModelAdmin):
    """Admin interface for rate limit logs"""
    
    list_display = ('endpoint', 'identifier', 'attempts', 'limit', 'is_blocked_badge', 'window_start', 'created_at')
    list_filter = ('is_blocked', 'endpoint', 'created_at')
    search_fields = ('endpoint', 'identifier')
    readonly_fields = ('endpoint', 'identifier', 'attempts', 'limit', 'window_start', 'window_end', 'is_blocked', 'created_at')
    date_hierarchy = 'created_at'
    list_per_page = 100
    
    def is_blocked_badge(self, obj):
        if obj.is_blocked:
            return '<span style="color: red;">🚫 مسدود</span>'
        return '<span style="color: green;">✓ فعال</span>'
    is_blocked_badge.short_description = 'وضعیت'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    """Admin interface for data access logs"""
    
    list_display = ('table_name', 'user_link', 'company_link', 'access_type_badge', 'record_id', 'rows_affected', 'timestamp')
    list_filter = ('access_type', 'table_name', 'timestamp', 'company')
    search_fields = ('user__username', 'table_name', 'query_snippet')
    readonly_fields = ('user', 'company', 'table_name', 'record_id', 'access_type', 'fields_accessed', 'query_snippet', 'rows_affected', 'timestamp')
    date_hierarchy = 'timestamp'
    list_per_page = 100
    
    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="?q={}">{}</a>', obj.user.username, obj.user)
        return 'سیستم'
    user_link.short_description = 'کاربر'
    
    def company_link(self, obj):
        if obj.company:
            return format_html('<a href="?company_id={}">{}</a>', obj.company.id, obj.company.name)
        return '-'
    company_link.short_description = 'شرکت'
    
    def access_type_badge(self, obj):
        colors = {
            'READ': 'blue',
            'WRITE': 'green',
            'DELETE': 'red',
            'EXPORT': 'orange',
        }
        color = colors.get(obj.access_type, 'gray')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_access_type_display())
    access_type_badge.short_description = 'نوع دسترسی'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Register models with custom titles
admin.site.site_title = 'پنل مدیریت امنیت فرمان'
admin.site.site_header = 'مدیریت امنیت پلتفرم فرمان'
admin.site.index_title = 'داشبورد مدیریت امنیت'
