__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.urls import reverse
from django.utils import timezone

from .constants import POTENTIAL_FELLOWSHIP_STATUSES,\
    POTENTIAL_FELLOWSHIP_IDENTIFIED, POTENTIAL_FELLOWSHIP_EVENTS
from .managers import FellowQuerySet, PotentialFellowshipQuerySet

from profiles.models import Profile

from scipost.behaviors import TimeStampedModel
from scipost.constants import SCIPOST_DISCIPLINES, DISCIPLINE_PHYSICS,\
    SCIPOST_SUBJECT_AREAS, TITLE_CHOICES
from scipost.fields import ChoiceArrayField
from scipost.models import get_sentinel_user, Contributor


class Fellowship(TimeStampedModel):
    """A Fellowship gives access to the Submission Pool to Contributors.

    Editorial College Fellowship connects the Editorial College and Contributors,
    possibly with a limiting start/until date and/or a Proceedings event.

    The date range will effectively be used while determining 'the pool' for a specific
    Submission, so it has a direct effect on the submission date.
    """

    contributor = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                    related_name='fellowships')
    start_date = models.DateField(null=True, blank=True)
    until_date = models.DateField(null=True, blank=True)

    guest = models.BooleanField('Guest Fellowship', default=False)

    objects = FellowQuerySet.as_manager()

    class Meta:
        ordering = ['contributor__user__last_name']
        unique_together = ('contributor', 'start_date', 'until_date')

    def __str__(self):
        _str = self.contributor.__str__()
        if self.guest:
            _str += ' (guest fellowship)'
        return _str

    def get_absolute_url(self):
        """Return the admin fellowship page."""
        return reverse('colleges:fellowship_detail', kwargs={'pk': self.id})

    def sibling_fellowships(self):
        """Return all Fellowships that are directly related to the Fellow of this Fellowship."""
        return self.contributor.fellowships.all()

    def is_active(self):
        """Check if the instance is within start and until date."""
        today = datetime.date.today()
        if not self.start_date:
            if not self.until_date:
                return True
            return today <= self.until_date
        elif not self.until_date:
            return today >= self.start_date
        return today >= self.start_date and today <= self.until_date


class PotentialFellowship(models.Model):
    """
    A PotentialFellowship is defined when a researcher has been identified by
    Admin or EdAdmin as a potential member of an Editorial College,
    or when a current Advisory Board member or Fellow nominates the person.

    It is linked to Profile as ForeignKey and not as OneToOne, since the same
    person can eventually be approached on different occasions.

    Using Profile allows to treat both registered Contributors
    and non-registered people equally well.
    """

    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=POTENTIAL_FELLOWSHIP_STATUSES,
                              default=POTENTIAL_FELLOWSHIP_IDENTIFIED)
    in_agreement = models.ManyToManyField(
        'scipost.Contributor',
        related_name='in_agreement_with_election', blank=True)
    in_abstain = models.ManyToManyField(
        'scipost.Contributor',
        related_name='in_abstain_with_election', blank=True)
    in_disagreement = models.ManyToManyField(
        'scipost.Contributor',
        related_name='in_disagreement_with_election', blank=True)
    voting_deadline = models.DateTimeField('voting deadline', default=timezone.now)
    elected = models.NullBooleanField()

    objects = PotentialFellowshipQuerySet.as_manager()

    class Meta:
        ordering = ['profile__last_name']

    def __str__(self):
        return '%s, %s' % (self.profile.__str__(), self.get_status_display())

    def latest_event_details(self):
        event = self.potentialfellowshipevent_set.order_by('-noted_on').first()
        if not event:
            return 'No event recorded'
        return '%s [%s]' % (event.get_event_display(), event.noted_on.strftime('%Y-%m-%d'))


class PotentialFellowshipEvent(models.Model):
    """Any event directly related to a PotentialFellowship instance registered as plain text."""

    potfel = models.ForeignKey('colleges.PotentialFellowship', on_delete=models.CASCADE)
    event = models.CharField(max_length=32, choices=POTENTIAL_FELLOWSHIP_EVENTS)
    comments = models.TextField(blank=True)

    noted_on = models.DateTimeField(auto_now_add=True)
    noted_by = models.ForeignKey('scipost.Contributor',
                                 on_delete=models.SET(get_sentinel_user),
                                 blank=True, null=True)

    def __str__(self):
        return '%s, %s %s: %s' % (self.potfel.profile.last_name,
                                  self.potfel.profile.get_title_display(),
                                  self.potfel.profile.first_name,
                                  self.get_event_display())
