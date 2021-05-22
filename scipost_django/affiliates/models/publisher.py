__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class AffiliatePublisher(models.Model):
    """
    A Publisher which piggybacks on SciPost's services.
    """

    name = models.CharField(
        max_length=256
    )

    class Meta:
        ordering = [
            'name'
        ]

    def __str__(self):
        return self.name
