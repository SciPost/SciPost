__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.db import models


class UserTag(models.Model):
    VARIANT_PRIMARY = 'primary'
    VARIANT_SECONDARY = 'secondary'
    VARIANT_SUCCESS = 'success'
    VARIANT_WARNING = 'warning'
    VARIANT_DANGER = 'danger'
    VARIANT_INFO = 'info'
    VARIANT_LIGHT = 'light'
    VARIANT_DARK = 'dark'
    VARIANT_CHOICES = (
        (VARIANT_PRIMARY, 'primary'),
        (VARIANT_SECONDARY, 'secondary'),
        (VARIANT_SUCCESS, 'success'),
        (VARIANT_WARNING, 'warning'),
        (VARIANT_DANGER, 'danger'),
        (VARIANT_INFO, 'info'),
        (VARIANT_LIGHT, 'light'),
        (VARIANT_DARK, 'dark'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='email_tags',
        on_delete=models.CASCADE)
    label = models.CharField(max_length=64)
    unicode_symbol = models.CharField(max_length=1, blank=True)
    variant = models.CharField(
        max_length=16,
        choices=VARIANT_CHOICES,
        default=VARIANT_INFO)
