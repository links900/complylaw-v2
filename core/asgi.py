# core/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import scanner.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Create the Django ASGI application once
django_asgi_app = get_asgi_application()

# Final ASGI application with WebSockets
application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AuthMiddlewareStack(
        URLRouter(
            scanner.routing.websocket_urlpatterns
        )
    ),
})
