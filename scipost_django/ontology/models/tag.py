__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class Tag(models.Model):
    """
    Tags can be attached to a Topic to specify which category it fits.
    Examples: Concept, Device, Model, Theory, ...
    """

    name = models.CharField(max_length=32, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
