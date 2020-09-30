_copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class Specialty(models.Model):
    """
    A principal division of an AcademicField.
    """

    acad_field = models.ForeignKey(
        'ontology.AcademicField',
        on_delete=models.CASCADE,
        related_name='specialties'
    )

    name = models.CharField(
        max_length=128
    )

    slug = models.SlugField(
        unique=True,
        allow_unicode=True
    )

    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['acad_field', 'order'],
                name='unique_acad_field_order'
            ),
        ]
        ordering = [
            'acad_field',
            'order',
        ]
        verbose_name_plural = 'specialties'

    def __str__(self):
        return self.name

    @property
    def code(self):
        """
        Capitalized letter code representing the specialty.
        """
        return self.slug.partition('-')[2].upper()
