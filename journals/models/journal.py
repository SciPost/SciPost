__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import Avg, F
from django.urls import reverse

from ..constants import JOURNAL_STRUCTURE, ISSUES_AND_VOLUMES, ISSUES_ONLY
from ..managers import JournalQuerySet
from ..validators import doi_journal_validator


class Journal(models.Model):
    """Journal is a container of Publications with a unique issn and doi_label.

    Publications may be categorized into issues or issues and volumes.
    """

    name = models.CharField(max_length=256, unique=True)
    name_abbrev = models.CharField(max_length=128, default='SciPost [abbrev]',
                                   help_text='Abbreviated name (for use in citations)')
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_journal_validator])
    issn = models.CharField(max_length=16, default='2542-4653', blank=True)
    active = models.BooleanField(default=True)
    structure = models.CharField(max_length=2,
                                 choices=JOURNAL_STRUCTURE, default=ISSUES_AND_VOLUMES)
    refereeing_period = models.DurationField(default=datetime.timedelta(days=28))

    objects = JournalQuerySet.as_manager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return Journal's homepage url."""
        return reverse('scipost:landing_page', args=(self.doi_label,))

    @property
    def doi_string(self):
        """Return DOI including the SciPost registrant prefix."""
        return '10.21468/' + self.doi_label

    @property
    def has_issues(self):
        return self.structure in (ISSUES_AND_VOLUMES, ISSUES_ONLY)

    @property
    def has_volumes(self):
        return self.structure in (ISSUES_AND_VOLUMES)

    def get_issues(self):
        from journals.models import Issue
        if self.structure == ISSUES_AND_VOLUMES:
            return Issue.objects.filter(in_volume__in_journal=self).published()
        elif self.structure == ISSUES_ONLY:
            return self.issues.open_or_published()
        return Issue.objects.none()

    def get_latest_issue(self):
        """Get latest existing Issue in database irrespective of its status."""
        from journals.models import Issue
        if self.structure == ISSUES_ONLY:
            return self.issues.order_by('-until_date').first()
        if self.structure == ISSUES_AND_VOLUMES:
            return Issue.objects.filter(in_volume__in_journal=self).order_by('-until_date').first()
        return None

    def get_latest_volume(self):
        """Get latest existing Volume in database irrespective of its status."""
        if self.structure == ISSUES_AND_VOLUMES:
            return self.volumes.order_by('-until_date').first()
        return None

    def get_publications(self):
        from journals.models import Publication
        if self.structure == ISSUES_AND_VOLUMES:
            return Publication.objects.filter(in_issue__in_volume__in_journal=self)
        elif self.structure == ISSUES_ONLY:
            return Publication.objects.filter(in_issue__in_journal=self)
        return self.publications.all()

    def nr_publications(self, tier=None):
        from journals.models import Publication
        publications = Publication.objects.filter(in_issue__in_volume__in_journal=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        return publications.count()

    def avg_processing_duration(self):
        from journals.models import Publication
        duration = Publication.objects.filter(
            in_issue__in_volume__in_journal=self).aggregate(
                avg=Avg(F('publication_date') - F('submission_date')))['avg']
        if duration:
            return duration.total_seconds() / 86400
        return 0

    def citation_rate(self, tier=None):
        """Return the citation rate in units of nr citations per article per year."""
        from journals.models import Publication
        publications = Publication.objects.filter(in_issue__in_volume__in_journal=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        ncites = 0
        deltat = 1  # to avoid division by zero
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                ncites += len(pub.citedby)
                deltat += (pub.latest_citedby_update.date() - pub.publication_date).days
        return (ncites * 365.25/deltat)

    def citedby_impact_factor(self, year):
        """Compute the impact factor for a given year YYYY, from Crossref cited-by data.

        This is defined as the total number of citations in year YYYY
        for all papers published in years YYYY-1 and YYYY-2, divided
        by the number of papers published in year YYYY.
        """
        publications = self.get_publications().filter(
            models.Q(publication_date__year=int(year)-1) |
            models.Q(publication_date__year=int(year)-2))
        nrpub = publications.count()
        if nrpub == 0:
            return 0
        ncites = 0
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                for citation in pub.citedby:
                    if citation['year'] == year:
                        ncites += 1
        return ncites / nrpub
