__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from typing import TYPE_CHECKING

from django.db import models
from django.urls import reverse
from ontology.models import Specialty

if TYPE_CHECKING:
    from colleges.models import FellowshipNomination
    from django.db.models.manager import RelatedManager
    from ontology.models.academic_field import AcademicField


class College(models.Model):
    """
    Anchor for a set of Fellows handling a set of Journals.

    A College has a ForeignKey to AcademicField.

    Specialties are defined as a `@property` and extracted via the Journals
    which are ForeignKey-related back to College.

    The `@property` `is_field_wide` checks the Journals run by the College and
    returns a Boolean specifying whether the College operates field-wide, or is specialized.
    """

    nominations: "RelatedManager[FellowshipNomination]"

    name = models.CharField(
        max_length=256,
        help_text="Official name of the College (default: name of the academic field)",
        unique=True,
    )

    acad_field = models.ForeignKey["AcademicField"](
        "ontology.AcademicField", on_delete=models.PROTECT, related_name="colleges"
    )

    slug = models.SlugField(unique=True, allow_unicode=True)

    order = models.PositiveSmallIntegerField()

    if TYPE_CHECKING:
        from journals.models import Journal

        journals: "RelatedManager[Journal]"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name",
                    "acad_field",
                ],
                name="college_unique_name_acad_field",
            ),
            models.UniqueConstraint(
                fields=["acad_field", "order"], name="college_unique_acad_field_order"
            ),
        ]
        ordering = ["acad_field", "order"]

    def __str__(self):
        return "Editorial College (%s)" % self.name

    def get_absolute_url(self):
        return reverse("colleges:college_detail", kwargs={"college": self.slug})

    @property
    def specialties(self):
        return Specialty.objects.filter(journals__college__pk=self.id).distinct()

    @property
    def is_hosted_journal(self):
        """
        Check if the College is exists for a hosted journal.
        In practice this is when the name does not match the academic field.
        """
        return self.name != self.acad_field.name

    @property
    def is_field_wide(self):
        return len(self.specialties) == 0
