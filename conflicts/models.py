__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import ValidationError
from django.db import models

from .constants import (
    CONFLICT_OF_INTEREST_STATUSES, STATUS_UNVERIFIED, CONFLICT_OF_INTEREST_TYPES, TYPE_OTHER)
from .managers import ConflictOfInterestQuerySet


class ConflictGroup(models.Model):
    """Group of related ConflictOfInterest objects linking conflicts based on meta data."""

    url = models.URLField(blank=True)
    title = models.CharField(max_length=256)

    related_submissions = models.ManyToManyField(
        'submissions.Submission', blank=True, related_name='conflict_groups')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Conflict group {}'.format(self.title[:30])


class ConflictOfInterest(models.Model):
    """Conflict of Interest is a flagged relation between scientists."""

    status = models.CharField(
        max_length=16, choices=CONFLICT_OF_INTEREST_STATUSES, default=STATUS_UNVERIFIED)
    origin = models.ForeignKey('scipost.Contributor')
    to_contributor = models.ForeignKey(
        'scipost.Contributor', blank=True, null=True, related_name='+')
    to_name = models.CharField(max_length=128, blank=True)
    type = models.CharField(
        max_length=16, choices=CONFLICT_OF_INTEREST_TYPES, default=TYPE_OTHER)

    conflict_group = models.ForeignKey('conflicts.ConflictGroup', null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = ConflictOfInterestQuerySet.as_manager()

    class Meta:
        default_related_name = 'conflicts'

    def __str__(self):
        _str = '{} {} to {}'.format(self.get_type_display(), self.origin, self.to_name)
        return _str

    def clean(self):
        """Check if Conflict of Interest is complete."""
        if not self.to_contributor and not self.to_unregistered:
            raise ValidationError(
                'Conflict of Interest must be related to Contributor or UnregisteredAuthor.')
