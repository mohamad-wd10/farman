"""
Django Signals for Security Module
Handles security-related events and automated responses
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_save, sender=User)
def user_created_signal(sender, instance, created, **kwargs):
    """Log when a new user is created"""
    if created:
        logger.info(f'New user created: {instance.username} ({instance.email})')
        
        # Log to audit trail
        try:
            from apps.security.models import AuditLog
            AuditLog.objects.create(
                user=instance,
                action_type='CREATE_DATA',
                action_name='ایجاد کاربر جدید',
                details={
                    'username': instance.username,
                    'email': instance.email,
                },
                is_suspicious=False
            )
        except Exception as e:
            logger.error(f'Error creating audit log for new user: {e}')


# Add more signals as needed for other models
