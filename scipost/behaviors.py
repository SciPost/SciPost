from django.db import models
from django.utils import timezone

from .db.fields import AutoDateTimeField


class TimeStampedModel(models.Model):
    """
    All objects should inherit from this abstract model.
    This will ensure the creation of created and modified
    timestamps in the objects.
    """
    created = models.DateTimeField(default=timezone.now)
    latest_activity = AutoDateTimeField(default=timezone.now)

    class Meta:
        abstract = True
