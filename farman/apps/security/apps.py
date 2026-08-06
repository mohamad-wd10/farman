"""
Django Apps Configuration for Security Module
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SecurityConfig(AppConfig):
    """Configuration class for security app"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.security'
    verbose_name = _('امنیت و حسابرسی')
    
    def ready(self):
        """Initialize security module"""
        # Import signals if needed
        from . import signals
        
        # Log startup
        import logging
        logger = logging.getLogger(__name__)
        logger.info('Security module initialized')
