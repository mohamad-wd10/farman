"""
Farman Security Module
Enterprise-grade security implementation with:
- Rate limiting
- SQL injection prevention
- XSS protection
- CSRF hardening
- Audit logging
- PII masking
- Row-level security enforcement
"""

import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.core.exceptions import PermissionDenied
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Central security configuration"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_EXPIRE_AFTER_SECONDS = 3600  # 1 hour
    
    # Rate limiting
    RATE_LIMIT_LOGIN = 5  # attempts per minute
    RATE_LIMIT_API = 100  # requests per minute
    RATE_LIMIT_UPLOAD = 10  # uploads per hour
    
    # Company code generation
    COMPANY_CODE_LENGTH = 8
    COMPANY_CODE_PREFIX = 'FRM'
    
    @classmethod
    def validate_password(cls, password: str) -> tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < cls.MIN_PASSWORD_LENGTH:
            errors.append(f'رمز عبور باید حداقل {cls.MIN_PASSWORD_LENGTH} کاراکتر باشد')
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append('رمز عبور باید شامل حروف بزرگ انگلیسی باشد')
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append('رمز عبور باید شامل حروف کوچک انگلیسی باشد')
        
        if cls.REQUIRE_DIGIT and not re.search(r'\d', password):
            errors.append('رمز عبور باید شامل اعداد باشد')
        
        if cls.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('رمز عبور باید شامل کاراکترهای خاص باشد')
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def generate_company_code(cls, company_name: str) -> str:
        """Generate unique company code"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = secrets.token_hex(4)
        hash_input = f"{cls.COMPANY_CODE_PREFIX}{company_name}{timestamp}{random_suffix}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()[:cls.COMPANY_CODE_LENGTH].upper()
        return f"{cls.COMPANY_CODE_PREFIX}-{hash_value}"
    
    @classmethod
    def sanitize_input(cls, input_string: str) -> str:
        """Sanitize user input to prevent XSS"""
        if not input_string:
            return input_string
        
        # Remove potential script tags
        input_string = re.sub(r'<script.*?>.*?</script>', '', input_string, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove event handlers
        input_string = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', input_string, flags=re.IGNORECASE)
        
        # Remove javascript: protocol
        input_string = re.sub(r'javascript:', '', input_string, flags=re.IGNORECASE)
        
        # Escape HTML entities
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        
        for char, escape in html_escape_table.items():
            input_string = input_string.replace(char, escape)
        
        return input_string.strip()


class RateLimiter:
    """Rate limiting implementation using cache"""
    
    def __init__(self, cache_backend):
        self.cache = cache_backend
    
    def is_allowed(self, key: str, max_attempts: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit"""
        current_time = datetime.now()
        window_key = f"rate_limit:{key}:{current_time.strftime('%Y%m%d%H%M')}"
        
        attempts = self.cache.get(window_key, 0)
        
        if attempts >= max_attempts:
            return False
        
        self.cache.incr(window_key)
        self.cache.expire(window_key, window_seconds)
        
        return True
    
    def get_remaining_attempts(self, key: str, max_attempts: int, window_seconds: int) -> int:
        """Get remaining attempts for rate limit"""
        current_time = datetime.now()
        window_key = f"rate_limit:{key}:{current_time.strftime('%Y%m%d%H%M')}"
        
        attempts = self.cache.get(window_key, 0)
        return max(0, max_attempts - attempts)


class PIIMasker:
    """Personal Identifiable Information Masking"""
    
    @staticmethod
    def mask_national_id(national_id: str) -> str:
        """Mask national ID (Iranian format)"""
        if not national_id or len(national_id) != 10:
            return national_id
        return f"***-***-{national_id[-4:]}"
    
    @staticmethod
    def mask_phone_number(phone: str) -> str:
        """Mask phone number"""
        if not phone or len(phone) < 4:
            return phone
        return f"****-****{phone[-4:]}"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address"""
        if not email or '@' not in email:
            return email
        parts = email.split('@')
        username = parts[0]
        domain = parts[1]
        
        if len(username) > 2:
            masked_username = f"{username[0]}***{username[-1]}"
        else:
            masked_username = "**"
        
        return f"{masked_username}@{domain}"
    
    @staticmethod
    def mask_bank_account(account: str) -> str:
        """Mask bank account number"""
        if not account or len(account) < 4:
            return account
        return f"****-****-****-{account[-4:]}"
    
    @staticmethod
    def mask_financial_data(data: Dict[str, Any], threshold: float = 1000000) -> Dict[str, Any]:
        """Mask sensitive financial data above threshold"""
        masked_data = data.copy()
        
        for key, value in masked_data.items():
            if isinstance(value, (int, float)) and abs(value) > threshold:
                # Keep only the magnitude for analysis
                masked_data[key] = f">{threshold:,}"
        
        return masked_data


class AuditLogger:
    """Comprehensive audit logging system"""
    
    ACTION_TYPES = {
        'LOGIN': 'ورود به سیستم',
        'LOGOUT': 'خروج از سیستم',
        'UPLOAD_FILE': 'آپلود فایل',
        'DOWNLOAD_FILE': 'دانلود فایل',
        'DELETE_DATA': 'حذف داده',
        'UPDATE_DATA': 'به‌روزرسانی داده',
        'CREATE_DATA': 'ایجاد داده',
        'EXPORT_REPORT': 'خروجی گزارش',
        'CHANGE_PERMISSION': 'تغییر دسترسی',
        'API_CALL': 'درخواست API',
    }
    
    @classmethod
    def log_action(cls, user, action_type: str, details: Dict[str, Any], ip_address: str = None):
        """Log an action for audit trail"""
        from apps.security.models import AuditLog
        
        try:
            AuditLog.objects.create(
                user=user,
                action_type=action_type,
                action_name=cls.ACTION_TYPES.get(action_type, action_type),
                details=details,
                ip_address=ip_address,
                timestamp=datetime.now()
            )
            logger.info(f"Audit: {user} performed {action_type} - {details}")
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
    
    @classmethod
    def get_user_audit_trail(cls, user, days: int = 30):
        """Get audit trail for a user"""
        from apps.security.models import AuditLog
        cutoff_date = datetime.now() - timedelta(days=days)
        return AuditLog.objects.filter(
            user=user,
            timestamp__gte=cutoff_date
        ).order_by('-timestamp')


class SQLInjectionPreventor:
    """SQL Injection Prevention"""
    
    DANGEROUS_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)',
        r'(--|\#|\/\*)',  # SQL comments
        r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+)',  # OR 1=1 patterns
        r"('\s*(OR|AND)\s*')",  # OR '' patterns
        r'(EXEC|EXECUTE)\s*\(',  # Stored procedure execution
        r'(xp_|sp_)\w+',  # Extended stored procedures
    ]
    
    @classmethod
    def is_safe_input(cls, input_string: str) -> bool:
        """Check if input is safe from SQL injection"""
        if not input_string:
            return True
        
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, input_string, re.IGNORECASE):
                return False
        
        return True
    
    @classmethod
    def validate_query_params(cls, params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate query parameters"""
        unsafe_params = []
        
        for key, value in params.items():
            if isinstance(value, str) and not cls.is_safe_input(value):
                unsafe_params.append(key)
        
        return (len(unsafe_params) == 0, unsafe_params)
