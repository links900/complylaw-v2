from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings
from django.contrib.sites.models import Site

@receiver(post_migrate)
def update_site(sender, **kwargs):
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            "domain": getattr(settings, "SITE_DOMAIN", "localhost:8000"),
            "name": getattr(settings, "SITE_NAME", "ComplyLaw")
        }
    )
