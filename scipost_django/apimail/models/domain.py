_copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from ..managers import DomainQuerySet
from ..validators import _simple_domain_name_validator


class Domain(models.Model):
    """
    Domain name information.
    """

    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = ((STATUS_ACTIVE, "Active"), (STATUS_ARCHIVED, "Archived"))

    name = models.CharField(
        max_length=100,
        validators=[_simple_domain_name_validator],
        unique=True,
    )
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )

    objects = DomainQuerySet.as_manager()

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
