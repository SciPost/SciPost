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


def cost_default_value():
    return { 'default': 400 }


class Journal(models.Model):
    """Journal is a container of Publications, with a unique issn and doi_label.

    Publications may be categorized into issues or issues and volumes.

    Each Journal falls under the auspices of a specific College, which is ForeignKeyed.
    The only exception is Selections, which does not point to any College
    (in fact: it falls under the auspices of all colleges at the same time).

    A Journal's AcademicField is indirectly specified via the College, since
    College has a ForeignKey to AcademicField.

    Specialties can optionally be specified (and should be consistent with the
    College's `acad_field`). If none are given, the Journal operates field-wide.
    """

    college = models.ForeignKey(
        'colleges.College',
        on_delete=models.PROTECT,
        related_name='journals'
    )

    specialties = models.ManyToManyField(
        'ontology.Specialty',
        blank=True,
        related_name='journals'
    )

    name = models.CharField(max_length=256, unique=True)
    name_abbrev = models.CharField(max_length=128, default='SciPost [abbrev]',
                                   help_text='Abbreviated name (for use in citations)')
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_journal_validator])
    issn = models.CharField(max_length=16, default='2542-4653', blank=True)
    active = models.BooleanField(default=True)
    submission_allowed = models.BooleanField(default=True)
    structure = models.CharField(max_length=2,
                                 choices=JOURNAL_STRUCTURE, default=ISSUES_AND_VOLUMES)
    refereeing_period = models.DurationField(default=datetime.timedelta(days=28))

    style = models.TextField(blank=True, null=True,
                             help_text=('CSS styling for the journal; the Journal\'s DOI '
                                        'should be used as class'))

    # For Journals list page
    blurb = models.TextField(default='[To be filled in; you can use markup]')
    list_order = models.PositiveSmallIntegerField(default=100)
    # For about page:
    description = models.TextField(default='[To be filled in; you can use markup]')
    scope = models.TextField(default='[To be filled in; you can use markup]')
    content = models.TextField(default='[To be filled in; you can use markup]')
    acceptance_criteria = models.TextField(default='[To be filled in; you can use markup]')
    submission_insert = models.TextField(blank=True, null=True,
                                         default='[Optional; you can use markup]')
    minimal_nr_of_reports = models.PositiveSmallIntegerField(
        help_text=('Minimal number of substantial Reports required '
                   'before an acceptance motion can be formulated'),
        default=1)

    has_DOAJ_Seal = models.BooleanField(default=False)

    # Templates
    template_latex_tgz = models.FileField(
        verbose_name='Template (LaTeX, gzipped tarball)',
        help_text='Gzipped tarball of the LaTeX template package',
        upload_to='UPLOADS/TEMPLATES/latex/%Y/', max_length=256, blank=True)

    # Cost per publication information
    cost_info = JSONField(default=cost_default_value)

    objects = JournalQuerySet.as_manager()

    class Meta:
        ordering = ['college__acad_field', 'list_order']

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

    def nr_publications(self, tier=None, year=None):
        from journals.models import Publication
        publications = self.get_publications()
        if year:
            publications = publications.filter(publication_date__year=year)
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
        publications = self.get_publications()
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

    def nr_citations(self, year):
        publications = self.get_publications()
        ncites = 0
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                for citation in pub.citedby:
                    if citation['year'] == str(year):
                        ncites += 1
        return ncites
    
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
                    if citation['year'] == str(year):
                        ncites += 1
        return ncites / nrpub

    def citedby_citescore(self, year):
        """Compute the CiteScore for a given year YYYY, from Crossref cited-by data.

        This is defined as the total number of citations in years YYYY to YYYY-3
        for all papers published in years YYYY to YYYY-3, divided
        by the number of papers published in that same set of years.
        """
        publications = self.get_publications().filter(
            publication_date__year__lte=int(year),
            publication_date__year__gte=int(year)-3)
        nrpub = publications.count()
        if nrpub == 0:
            return 0
        ncites = 0
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                for citation in pub.citedby:
                    if int(citation['year']) <= year and int(citation['year']) >= year - 3:
                        ncites += 1
        return ncites / nrpub
    
    def cost_per_publication(self, year):
        try:
            return int(self.cost_info[str(year)])
        except KeyError:
            return int(self.cost_info['default'])
