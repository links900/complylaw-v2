# core/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import public_home
from django.views.generic import TemplateView 
from users.views import CustomSignupView


urlpatterns = [
    path('admin/', admin.site.urls),
    
    
    # === ALLAUTH — FINAL FIX THAT CANNOT FAIL ===
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    
    # Now include the rest of allauth (login, password reset, etc.)
    path('accounts/', include('allauth.urls')),
    
    # Optional: keep the override for the old redirect (harmless but not needed anymore)
    # path('accounts/confirm-email/', TemplateView.as_view(
    #     template_name="account/email_confirmation_sent.html"
    # ), name="account_email_confirmation_sent"),
    
    
    
    # App URLs
    
    # PRICING FIRST — MUST BE BEFORE ANY CATCH-ALL
    
    path('pricing/', include('billing.urls', namespace='billing')),  # ← THIS LINE FIRST
    #path('billing/', include('billing.urls', namespace='billing')),
    
    
    # YOUR PROFILE PAGE — THIS WAS MISSING!
    path('profile/', include('users.urls')),

    # ROOT URL → Public marketing page (only for non-logged-in users)
    path('', public_home, name='home'),  # This wins — placed BEFORE dashboard include

    # Dashboard app handles /dashboard/ AND also serves as fallback at root for logged-in users
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    #path('', include('dashboard.urls')),  # This keeps your old behavior (optional, safe to keep)
    
    
    #path('users/', include('users.urls')),
    path('scanner/', include('scanner.urls')),
    path('reports/', include('reports.urls')),
    
    path('ws/', include('dashboard.routing')),
    
    
    
    
    
    
    
    
    # WebSocket — REMOVE channels.urls
    # path('ws/', include('channels.urls')),  ← DELETE THIS LINE
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])