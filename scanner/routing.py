# scanner/routing.py
from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    # Live scan progress
    re_path(r'ws/scan/(?P<scan_id>[\w-]+)/$', consumers.ScanProgressConsumer.as_asgi()),
    
    # Global notifications (Grade A confetti, toasts, etc.)
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]