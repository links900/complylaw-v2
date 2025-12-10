# core/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
application = get_asgi_application()  # MUST BE FIRST

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from scanner.consumers import ScanProgressConsumer, NotificationConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            re_path(r'ws/scan/(?P<scan_id>[\w-]+)/$', ScanProgressConsumer.as_asgi()),
            re_path(r'ws/notifications/$', NotificationConsumer.as_asgi()),  # THIS WAS MISSING
        ])
    ),
})