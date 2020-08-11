__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from scipost.constants import SCIPOST_DISCIPLINES
from scipost.fields import ChoiceArrayField


class PreprintServer(models.Model):
    """
    Representation of a SciPost-integrated preprint server which can be used upon submission.
    """
    name = models.CharField(max_length=256)
    url = models.URLField()
    disciplines = ChoiceArrayField(
        models.CharField(max_length=32, choices=SCIPOST_DISCIPLINES)
    )

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name
