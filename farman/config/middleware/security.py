"""
Custom Middleware for Farman Platform
Security, auditing, multi-tenancy, and performance monitoring
"""

import time
import json
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.shortcuts import redirect
import logging

from apps.security.core import (
    SecurityConfig,
    RateLimiter,
    SQLInjectionPreventor,
    AuditLogger,
    PIIMasker
)

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Main security middleware that handles:
    - SQL injection prevention
    - XSS protection
    - Rate limiting
    - Request validation
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limiter = RateLimiter(getattr(settings, 'CACHES', {}))
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process view before execution"""
        
        # Skip security checks for static files and media
        if request.path.startswith(('/static/', '/media/')):
            return None
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Rate limiting for login attempts
        if request.path == '/accounts/login/' and request.method == 'POST':
            identifier = f"login:{client_ip}"
            if not self.rate_limiter.is_allowed(
                identifier,
                SecurityConfig.RATE_LIMIT_LOGIN,
                60  # 1 minute window
            ):
                remaining = self.rate_limiter.get_remaining_attempts(
                    identifier,
                    SecurityConfig.RATE_LIMIT_LOGIN,
                    60
                )
                logger.warning(f"Rate limit exceeded for login from {client_ip}")
                
                # Log security event
                if hasattr(request, 'company'):
                    from apps.security.models import SecurityEvent
                    SecurityEvent.objects.create(
                        company=request.company,
                        event_type='BRUTE_FORCE',
                        severity='HIGH',
                        description=f'تلاش برای ورود بیش از حد مجاز از IP {client_ip}',
                        source_ip=client_ip,
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
                
                return JsonResponse({
                    'error': 'تعداد تلاش‌های شما بیش از حد است. لطفاً بعداً مجدداً تلاش کنید.',
                    'remaining_attempts': remaining
                }, status=429)
        
        # Validate query parameters for SQL injection
        all_params = {**request.GET.dict(), **request.POST.dict()}
        is_safe, unsafe_params = SQLInjectionPreventor.validate_query_params(all_params)
        
        if not is_safe:
            logger.warning(f"SQL injection attempt detected from {client_ip}. Unsafe params: {unsafe_params}")
            
            # Log security event
            if hasattr(request, 'company'):
                from apps.security.models import SecurityEvent
                SecurityEvent.objects.create(
                    company=request.company,
                    event_type='SQL_INJECTION',
                    severity='CRITICAL',
                    description=f'تلاش برای تزریق SQL detected. پارامترهای مشکوک: {", ".join(unsafe_params)}',
                    source_ip=client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                    metadata={'unsafe_params': unsafe_params}
                )
            
            return JsonResponse({
                'error': 'درخواست شما حاوی داده‌های نامعتبر است.'
            }, status=400)
        
        return None
    
    def process_response(self, request, response):
        """Add security headers to response"""
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy (adjust as needed)
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self';"
        )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MultiTenancyMiddleware(MiddlewareMixin):
    """
    Middleware for handling multi-tenancy based on company code
    Ensures data isolation between companies
    """
    
    def process_request(self, request):
        """Attach company to request based on user or session"""
        
        # Skip for authentication pages and static files
        if request.path.startswith(('/accounts/login', '/accounts/register', '/static/', '/media/')):
            return None
        
        # If user is authenticated, get their company
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Assuming user has a company relation
                if hasattr(request.user, 'company'):
                    request.company = request.user.company
                    # Set timezone based on company settings if needed
            except Exception as e:
                logger.error(f"Error fetching company for user {request.user}: {e}")
                request.company = None
        else:
            # Try to get company from session
            company_code = request.session.get('company_code')
            if company_code:
                try:
                    from apps.accounts.models import Company
                    request.company = Company.objects.get(code=company_code)
                except Company.DoesNotExist:
                    request.company = None
                    # Clear invalid session
                    request.session.pop('company_code', None)
        
        return None


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for automatic audit logging of all requests
    """
    
    def process_request(self, request):
        """Store request start time"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log the request after processing"""
        
        # Skip logging for static files and health checks
        if request.path.startswith(('/static/', '/media/', '/health/', '/favicon.ico')):
            return response
        
        # Calculate request duration
        duration = None
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
        
        # Log important actions asynchronously
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self.log_action(request, response, duration)
        
        return response
    
    def log_action(self, request, response, duration):
        """Log action to audit trail"""
        try:
            # Determine action type based on method and path
            action_type = self.determine_action_type(request)
            
            if action_type and hasattr(request, 'user') and request.user.is_authenticated:
                # Log asynchronously (in production, use Celery task)
                AuditLogger.log_action(
                    user=request.user,
                    action_type=action_type,
                    details={
                        'path': request.path,
                        'method': request.method,
                        'status_code': response.status_code,
                        'duration_ms': round(duration * 1000, 2) if duration else None,
                    },
                    ip_address=SecurityMiddleware.get_client_ip(request)
                )
        except Exception as e:
            logger.error(f"Error logging audit action: {e}")
    
    @staticmethod
    def determine_action_type(request):
        """Determine audit action type based on request"""
        path = request.path.lower()
        method = request.method
        
        if method == 'POST':
            if 'upload' in path:
                return 'UPLOAD_FILE'
            elif 'login' in path:
                return 'LOGIN'
            else:
                return 'CREATE_DATA'
        elif method in ['PUT', 'PATCH']:
            return 'UPDATE_DATA'
        elif method == 'DELETE':
            return 'DELETE_DATA'
        elif method == 'GET':
            if 'export' in path or 'download' in path:
                return 'EXPORT_REPORT'
        
        return None


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware for session security enhancements
    """
    
    def process_request(self, request):
        """Validate session security"""
        
        # Check session expiry
        if request.session.get_expiry_age() <= 0:
            logout(request)
            return redirect('accounts:login')
        
        # Optional: Check for suspicious session activity
        # (e.g., IP change, user agent change)
        session_ip = request.session.get('session_ip')
        if session_ip and session_ip != SecurityMiddleware.get_client_ip(request):
            # Log suspicious activity
            logger.warning(f"Session IP mismatch for user {getattr(request, 'user', None)}")
            # Optionally logout user
            # logout(request)
            # return redirect('accounts:login')
        
        # Store current IP in session
        request.session['session_ip'] = SecurityMiddleware.get_client_ip(request)
        
        return None
    
    def process_response(self, request, response):
        """Set secure session attributes"""
        
        # Ensure session cookies are secure
        request.session.modified = True
        
        return response
