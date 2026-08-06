"""
Farman Celery Application
Distributed Task Queue for AI Processing and Data Analysis
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farman.settings')

app = Celery('farman')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Periodic Tasks Configuration
app.conf.beat_schedule = {
    # Daily brief generation at 7:30 AM Tehran time
    'generate-daily-briefs': {
        'task': 'farman.ai_engine.tasks.generate_daily_briefs',
        'schedule': crontab(hour=7, minute=30),
    },
    
    # Company health score calculation every hour
    'calculate-company-health-scores': {
        'task': 'farman.analytics.tasks.calculate_company_health_scores',
        'schedule': crontab(minute=0),  # Every hour
    },
    
    # Check for upcoming checks and payments daily at 8 AM
    'check-upcoming-payments': {
        'task': 'farman.analytics.tasks.check_upcoming_payments',
        'schedule': crontab(hour=8, minute=0),
    },
    
    # Clean up old temporary files every Sunday at 2 AM
    'cleanup-temporary-files': {
        'task': 'farman.uploads.tasks.cleanup_temporary_files',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
    
    # Anomaly detection every 6 hours
    'run-anomaly-detection': {
        'task': 'farman.ai_engine.tasks.run_anomaly_detection',
        'schedule': crontab(minute=0, hour='*/6'),
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
