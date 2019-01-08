__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.urls import reverse
from django.utils import timezone

from .constants import POTENTIAL_FELLOWSHIP_STATUSES,\
    POTENTIAL_FELLOWSHIP_IDENTIFIED, POTENTIAL_FELLOWSHIP_EVENTS
from .managers import FellowQuerySet

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
        unique_together = ('contributor', 'start_date', 'until_date')

    def __str__(self):
        _str = self.contributor.__str__()
        if self.guest:
            _str += ' (guest fellowship)'
        return _str

    def get_absolute_url(self):
        """Return the admin fellowship page."""
        return reverse('colleges:fellowship', args=(self.id,))

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
    Admin or EdAdmin as a potential member of an Editorial College.

    It is linked to Profile as ForeignKey and not as OneToOne, since the same
    person can eventually be approached on different occasions.

    COMMENT: Why is this only nonregistered people only?
    """

    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=POTENTIAL_FELLOWSHIP_STATUSES,
                              default=POTENTIAL_FELLOWSHIP_IDENTIFIED)

    def __str__(self):
        return '%s, %s' % (self.profile.__str__(), self.get_status_display())


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
        return '%s, %s %s: %s' % (self.potfel.last_name, self.potfel.get_title_display(),
                                  self.potfel.first_name, self.get_event_display())
