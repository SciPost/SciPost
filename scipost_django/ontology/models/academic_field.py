_copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models

from journals.models import Journal


class AcademicField(models.Model):
    """
    A principal division of a branch of knowledge.
    """

    branch = models.ForeignKey(
        "ontology.Branch", on_delete=models.CASCADE, related_name="academic_fields"
    )

    name = models.CharField(max_length=128)

    slug = models.SlugField(unique=True, allow_unicode=True)

    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "order"], name="unique_branch_order"
            ),
        ]
        ordering = [
            "branch",
            "order",
        ]

    def __str__(self):
        return self.name

    @property
    def journals(self):
        return Journal.objects.filter(college__acad_field=self.id)
