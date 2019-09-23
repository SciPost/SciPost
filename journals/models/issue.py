__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, F
from django.utils import timezone
from django.urls import reverse

from proceedings.models import Proceedings

from ..constants import ISSUES_ONLY, ISSUE_STATUSES, STATUS_DRAFT, STATUS_PUBLISHED,\
    STATUS_PUBLICLY_OPEN
from ..managers import IssueQuerySet
from ..validators import doi_issue_validator



class Issue(models.Model):
    """
    An Issue is related to a specific Journal, either indirectly via a Volume
    container, or directly. It is a container for multiple Publications.
    """
    in_journal = models.ForeignKey(
        'journals.Journal', on_delete=models.CASCADE, null=True, blank=True,
        limit_choices_to={'structure': ISSUES_ONLY},
        help_text='Assign either a Volume or Journal to the Issue')
    in_volume = models.ForeignKey(
        'journals.Volume', on_delete=models.CASCADE, null=True, blank=True,
        help_text='Assign either a Volume or Journal to the Issue')
    number = models.PositiveIntegerField()
    slug = models.SlugField()
    start_date = models.DateField(default=timezone.now)
    until_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=ISSUE_STATUSES, default=STATUS_PUBLISHED)
    doi_label = models.CharField(max_length=200, unique=True, db_index=True,
                                 validators=[doi_issue_validator])

    # absolute path on filesystem: (JOURNALS_DIR)/journal/vol/issue/
    path = models.CharField(max_length=200)

    objects = IssueQuerySet.as_manager()

    class Meta:
        default_related_name = 'issues'
        ordering = ('-until_date',)
        unique_together = ('number', 'in_volume')

    def __str__(self):
        text = self.issue_string
        if hasattr(self, 'proceedings'):
            return text
        text += ' (%s)' % self.period_as_string
        if self.status == STATUS_DRAFT:
            text += ' (In draft)'
        return text

    def clean(self):
        """Check if either a Journal or Volume is assigned to the Issue."""
        if not (self.in_journal or self.in_volume):
            raise ValidationError({
                'in_journal': ValidationError('Either assign a Journal or Volume to this Issue',
                                              code='required'),
                'in_volume': ValidationError('Either assign a Journal or Volume to this Issue',
                                             code='required'),
            })
        if self.in_journal and not self.in_journal.has_issues:
            raise ValidationError({
                'in_journal': ValidationError('This journal does not allow for the use of Issues',
                                              code='invalid'),
            })

    def get_absolute_url(self):
        return reverse('scipost:issue_detail', args=[self.doi_label])

    @property
    def doi_string(self):
        return '10.21468/' + self.doi_label

    @property
    def issue_string(self):
        if self.in_volume:
            return '%s issue %s' % (self.in_volume, self.number)
        elif self.status == STATUS_PUBLICLY_OPEN:
            try:
                return '%s (open): %s (%s)' % (self.in_journal,
                                               self.proceedings.event_name, self.number)
            except Proceedings.DoesNotExist:
                pass
            return '%s (open): %s' % (self.in_journal, self.number)
        return '%s issue %s' % (self.in_journal, self.number)

    @property
    def short_str(self):
        if self.in_volume:
            return 'Vol. %s issue %s' % (self.in_volume.number, self.number)
        return 'Issue %s' % self.doi_label.rpartition('.')[2]

    @property
    def period_as_string(self):
        if self.start_date.month == self.until_date.month:
            return '%s %s' % (self.until_date.strftime('%B'), self.until_date.strftime('%Y'))
        return '%s - %s' % (self.start_date.strftime('%B'), self.until_date.strftime('%B %Y'))

    def get_journal(self):
        if self.in_journal:
            return self.in_journal
        return self.in_volume.in_journal

    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today and self.until_date >= today

    def nr_publications(self, tier=None):
        from journals.models import Publication
        publications = Publication.objects.filter(in_issue=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        return publications.count()

    def avg_processing_duration(self):
        from journals.models import Publication
        duration = Publication.objects.filter(
            in_issue=self).aggregate(
                avg=Avg(F('publication_date') - F('submission_date')))['avg']
        if duration:
            return duration.total_seconds() / 86400
        return 0

    def citation_rate(self, tier=None):
        """Return the citation rate in units of nr citations per article per year."""
        from journals.models import Publication
        publications = Publication.objects.filter(in_issue=self)
        if tier:
            publications = publications.filter(
                accepted_submission__eicrecommendations__recommendation=tier)
        ncites = 0
        deltat = 1  # to avoid division by zero
        for pub in publications:
            if pub.citedby and pub.latest_citedby_update:
                ncites += len(pub.citedby)
                deltat += (pub.latest_citedby_update.date() - pub.publication_date).days
        return (ncites * 365.25 / deltat)
