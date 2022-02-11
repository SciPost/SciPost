__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.core.validators import RegexValidator
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


orcid_validator = RegexValidator(
    r"^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$",
    "Please follow the ORCID format, e.g.: 0000-0001-2345-6789",
)
