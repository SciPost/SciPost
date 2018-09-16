__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.urls import reverse
from django.utils import timezone

from .constants import POTENTIAL_FELLOWSHIP_STATUSES,\
    POTENTIAL_FELLOWSHIP_IDENTIFIED, POTENTIAL_FELLOWSHIP_EVENTS,\
    PROSPECTIVE_FELLOW_STATUSES, PROSPECTIVE_FELLOW_IDENTIFIED,\
    PROSPECTIVE_FELLOW_EVENTS
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
    """
    profile = models.ForeignKey('profiles.Profile', on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=POTENTIAL_FELLOWSHIP_STATUSES,
                              default=POTENTIAL_FELLOWSHIP_IDENTIFIED)


class PotentialFellowshipEvent(models.Model):
    potfel = models.ForeignKey('colleges.PotentialFellowship', on_delete=models.CASCADE)
    event = models.CharField(max_length=32, choices=POTENTIAL_FELLOWSHIP_EVENTS)
    comments = models.TextField(blank=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey('scipost.Contributor',
                                 on_delete=models.SET(get_sentinel_user),
                                 blank=True, null=True)

    def __str__(self):
        return '%s, %s %s: %s' % (self.potfel.last_name, self.potfel.get_title_display(),
                                  self.potfel.first_name, self.get_event_display())


class ProspectiveFellow(models.Model):
    """
    A ProspectiveFellow is somebody who has been identified as
    a potential member of an Editorial College.
    """
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    discipline = models.CharField(max_length=20, choices=SCIPOST_DISCIPLINES,
                                  default=DISCIPLINE_PHYSICS, verbose_name='Main discipline')
    expertises = ChoiceArrayField(
        models.CharField(max_length=10, choices=SCIPOST_SUBJECT_AREAS),
        blank=True, null=True)
    webpage = models.URLField(blank=True)
    status = models.CharField(max_length=32, choices=PROSPECTIVE_FELLOW_STATUSES,
                              default=PROSPECTIVE_FELLOW_IDENTIFIED)
    contributor = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                    null=True, blank=True, related_name='+')

    class Meta:
        ordering = ['last_name']

    def __str__(self):
        return '%s, %s %s (%s)' % (self.last_name, self.get_title_display(), self.first_name,
                                   self.get_status_display())


class ProspectiveFellowEvent(models.Model):
    prosfellow = models.ForeignKey('colleges.ProspectiveFellow', on_delete=models.CASCADE)
    event = models.CharField(max_length=32, choices=PROSPECTIVE_FELLOW_EVENTS)
    comments = models.TextField(blank=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey('scipost.Contributor',
                                 on_delete=models.SET(get_sentinel_user),
                                 blank=True, null=True)

    def __str__(self):
        return '%s, %s %s: %s' % (self.prosfellow.last_name, self.prosfellow.get_title_display(),
                                  self.prosfellow.first_name, self.get_event_display())
