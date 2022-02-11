__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.utils import timezone


class AutoDateTimeField(models.DateTimeField):
    """Create an auto_now DateTimeField instead of auto_now."""

    def __init__(self, *args, **kwargs):
        kwargs["editable"] = False
        kwargs["blank"] = True
        super(AutoDateTimeField, self).__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        return timezone.now()
