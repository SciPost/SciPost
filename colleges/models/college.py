__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from scipost.constants import SCIPOST_DISCIPLINES

from ontology.models import Specialty


class College(models.Model):
    """
    Anchor for a set of Fellows handling a set of Journals.

    A College has a ForeignKey to AcademicField.

    Specialties are defined as a `@property` and extracted via the Journals
    which are ForeignKey-related back to College.

    The `@property` `is_field_wide` checks the Journals run by the College and
    returns a Boolean specifying whether the College operates field-wide, or is specialized.
    """

    name = models.CharField(
        max_length=256,
        help_text='Official name of the College (default: name of the discipline)',
        unique=True
    )

    acad_field = models.ForeignKey(
        'ontology.AcademicField',
        on_delete=models.PROTECT,
        related_name='colleges'
    )

    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'acad_field',],
                name='college_unique_name_acad_field'
            ),
            models.UniqueConstraint(
                fields=['acad_field', 'order'],
                name='college_unique_acad_field_order'
            ),
        ]
        ordering = [
            'acad_field',
            'order'
        ]

    def __str__(self):
        return "Editorial College (%s)" % self.name

    @property
    def specialties(self):
        return Specialty.objects.filter(journals__college__pk=self.id)

    @property
    def is_field_wide(self):
        return len(self.specialties) == 0
