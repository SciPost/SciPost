__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class UserTag(models.Model):
    """
    User-defined tag which can be attached to stored messages.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='email_tags',
        on_delete=models.CASCADE)
    label = models.CharField(max_length=16)
    text_color = models.CharField(
        max_length=7,
        default='#f6a11a',
        validators=[RegexValidator(regex='#[0-9a-f]{6}'),],
    )
    bg_color = models.CharField(
        max_length=7,
        default='#6885c3',
        validators=[RegexValidator(regex='#[0-9a-f]{6}'),],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['label', 'text_color', 'bg_color'],
                name='unique_label_colors'
                ),
        ]
        ordering = [
            'label',
        ]
