'''
# scanner/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    #re_path(r'ws/scan/(?P<scan_id>\d+)/$', consumers.ScanConsumer.as_asgi()),
    # or if you use scan_id as a string like '13b7616d':
    re_path(r'ws/scan/(?P<scan_id>[\w-]+)/$', consumers.ScanConsumer.as_asgi()),
    
    

]
'''

# scanner/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Live scan progress (per scan ID – supports both integer and UUID-like strings)
    re_path(r'ws/scan/(?P<scan_id>[\w-]+)/$', consumers.ScanProgressConsumer.as_asgi()),

    # Live notifications (toast messages like "apple.com scan completed!")
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi())
]