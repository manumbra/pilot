from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Site, DefaultHours, WEEKDAYS

@receiver(post_save, sender=Site)
def create_default_hours(sender, instance, created, **kwargs):
    """
    Automatically create 7 DefaultHours (one per weekday) when a Site is created.
    """
    if created:
        for day_index, day_name in WEEKDAYS:
            DefaultHours.objects.create(
                site=instance,
                weekday=day_index,
                is_closed=False
            )