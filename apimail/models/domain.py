_copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from ..validators import _simple_domain_name_validator


class Domain(models.Model):
    """
    Domain name information.
    """
    name = models.CharField(
        max_length=100,
        validators=[_simple_domain_name_validator],
        unique=True,
    )

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
