__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


class PreprintServer(models.Model):
    """
    Representation of a SciPost-integrated preprint server which can be used upon submission.
    """

    name = models.CharField(max_length=256)
    url = models.URLField()
    served_by = models.ForeignKey(
        "submissions.PreprintServer",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subsidiaries",
    )
    acad_fields = models.ManyToManyField(
        "ontology.AcademicField", blank=True, related_name="preprint_servers"
    )

    class Meta:
        ordering = [
            "name",
        ]

    def __str__(self):
        name = self.name
        if self.served_by:
            name = name + " (served by " + self.served_by.name + ")"
        return name
