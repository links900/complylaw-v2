# scanner/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class ScanProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.scan_id = self.scope["url_route"]["kwargs"]["scan_id"]
        self.room_group_name = f"scan_{self.scan_id}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # THIS IS THE CORRECT METHOD NAME (must match "type" in group_send)
    def scan_update(self, event):
        self.send(text_data=json.dumps({
            "progress": event.get("progress"),
            "step": event.get("step"),
            "status": event.get("status", "running")
        }))

    def scan_complete_trigger(self, event):
        self.send(text_data=json.dumps({
            "type": "complete",
            "force_reload": True,
            "progress": 100,
            "grade": event.get("grade"),
            "risk_score": event.get("risk_score")
        }))


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            self.close()
        else:
            # All authenticated users join the same group
            async_to_sync(self.channel_layer.group_add)(
                "global_notifications",   # ← this group name is used in tasks.py
                self.channel_name
            )
            self.accept()

    def disconnect(self, close_code):
        if not self.scope["user"].is_anonymous:
            async_to_sync(self.channel_layer.group_discard)(
                "global_notifications",
                self.channel_name
            )

    # THIS IS THE CORRECT METHOD NAME — must be called "send_notification"
    def send_notification(self, event):
        self.send(text_data=json.dumps({
            "type": "notification",
            "message": event["message"],
            "grade": event.get("grade"),
            "risk_score": event.get("risk_score"),
        }))