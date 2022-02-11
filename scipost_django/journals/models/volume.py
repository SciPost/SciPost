__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, F
from django.utils import timezone

from ..constants import ISSUES_AND_VOLUMES
from ..validators import doi_volume_validator


class Volume(models.Model):
    """
    A Volume belongs to a specific Journal, and is a container for
    either (multiple) Issue(s) or Publication(s).
    """

    in_journal = models.ForeignKey(
        "journals.Journal",
        limit_choices_to={"structure": ISSUES_AND_VOLUMES},
        on_delete=models.CASCADE,
    )
    number = models.PositiveSmallIntegerField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    doi_label = models.CharField(
        max_length=200, unique=True, db_index=True, validators=[doi_volume_validator]
    )

    class Meta:
        default_related_name = "volumes"
        ordering = ("-until_date",)
        unique_together = ("number", "in_journal")

    def __str__(self):
        return str(self.in_journal) + " Vol. " + str(self.number)

    def clean(self):
        """Check if the Volume is assigned to a valid Journal."""
        if not self.in_journal.has_volumes:
            raise ValidationError(
                {
                    "in_journal": ValidationError(
                        "This journal does not allow for the use of Volumes",
                        code="invalid",
                    ),
                }
            )

    @property
    def doi_string(self):
        return "10.21468/" + self.doi_label

    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today and self.until_date >= today

    def nr_publications(self, tier=None):
        from journals.models import Publication

        publications = Publication.objects.filter(in_issue__in_volume=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier
            )
        return publications.count()

    def avg_processing_duration(self):
        from journals.models import Publication

        duration = Publication.objects.filter(in_issue__in_volume=self).aggregate(
            avg=Avg(F("publication_date") - F("submission_date"))
        )["avg"]
        if duration:
            return duration.total_seconds() / 86400
        return 0

    def citation_rate(self, tier=None):
        """Returns the citation rate in units of nr citations per article per year."""
        from journals.models import Publication

        publications = Publication.objects.filter(in_issue__in_volume=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier
            )
        ncites = 0
        deltat = 1  # to avoid division by zero
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                ncites += len(pub.citedby)
                deltat += (pub.latest_citedby_update.date() - pub.publication_date).days
        return ncites * 365.25 / deltat
