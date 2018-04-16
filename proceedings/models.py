__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from scipost.behaviors import TimeStampedModel

from .managers import ProceedingsQuerySet

today = timezone.now().date()


class Proceedings(TimeStampedModel):
    """
    A Proceeding is a special kind of Journal Issue.
    """
    # Link to the actual Journal platform
    issue = models.OneToOneField('journals.Issue', related_name='proceedings',
                                 limit_choices_to={
                                    'in_volume__in_journal__name': 'SciPostPhysProc'})

    # Event the Proceedings is for
    event_name = models.CharField(max_length=256, blank=True)
    event_suffix = models.CharField(max_length=256, blank=True)
    event_description = models.TextField(blank=True)
    event_start_date = models.DateField(null=True, blank=True)
    event_end_date = models.DateField(null=True, blank=True)

    # Fellows
    lead_fellow = models.ForeignKey('colleges.Fellowship', null=True, blank=True, related_name='+')
    fellowships = models.ManyToManyField('colleges.Fellowship', blank=True,
                                         limit_choices_to={'guest': True})

    # Submission data
    submissions_open = models.DateField()
    submissions_deadline = models.DateField()
    submissions_close = models.DateField()

    objects = ProceedingsQuerySet.as_manager()

    class Meta:
        verbose_name = 'Proceedings'
        verbose_name_plural = 'Proceedings'
        default_related_name = 'proceedings'

    def __str__(self):
        _str = self.event_name
        if self.event_suffix:
            _str += ' ({s})'.format(s=self.event_suffix)
        return _str

    def get_absolute_url(self):
        return reverse('proceedings:proceedings_details', args=(self.id,))

    @property
    def open_for_submission(self):
        return self.submissions_open <= today and self.submissions_close >= today
