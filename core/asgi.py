# core/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from scanner.consumers import ScanProgressConsumer, NotificationConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r'ws/scan/(?P<scan_id>[\w-]+)/$', ScanProgressConsumer.as_asgi()),
            re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),
        ])
    ),
})
