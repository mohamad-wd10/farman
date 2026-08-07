"""
Farman - Enterprise AI Operating System for Business Management
URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Admin panel with custom styling
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Core authentication URLs
    path('api/auth/', include('farman.core.urls')),
    
    # Company management URLs
    path('api/companies/', include('farman.companies.urls')),
    
    # File upload and processing URLs
    path('api/uploads/', include('farman.uploads.urls')),
    
    # AI Engine URLs
    path('api/ai/', include('farman.ai_engine.urls')),
    
    # Analytics and reporting URLs
    path('api/analytics/', include('farman.analytics.urls')),
    
    # Public API endpoints
    path('api/v1/', include('farman.api.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error pages
handler404 = 'farman.core.views.error_404'
handler500 = 'farman.core.views.error_500'

# Admin site customization
admin.site.site_header = "پنل مدیریت فرمان"
admin.site.site_title = "فرمان | پنل مدیریت"
admin.site.index_title = "به سیستم مدیریت فرمان خوش آمدید"
