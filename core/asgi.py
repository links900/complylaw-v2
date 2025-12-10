# core/asgi.py
import os
from django.core.asgi import get_asgi_application

# MUST BE FIRST — initializes Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_asgi_application()

# NOW safe to import consumers
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path

# Import both consumers
from scanner.consumers import ScanProgressConsumer, NotificationConsumer

# Final ASGI application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # Scan progress (supports both int and string IDs)
            re_path(r'ws/scan/(?P<scan_id>[\w-]+)/$', ScanProgressConsumer.as_asgi()),

            # ← THIS WAS MISSING → Notifications toast
            re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
        ])
    ),
})