__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.core.exceptions import ValidationError
from django.db import models

from .constants import (
    CONFLICT_OF_INTEREST_STATUSES, STATUS_UNVERIFIED, CONFLICT_OF_INTEREST_TYPES, TYPE_OTHER)


class ConflictOfInterest(models.Model):
    """Conflict of Interest is a flagged relation between scientists."""

    status = models.CharField(
        max_length=16, choices=CONFLICT_OF_INTEREST_STATUSES, default=STATUS_UNVERIFIED)
    origin = models.ForeignKey('scipost.Contributor', related_name='conflicts')
    to_contributor = models.ForeignKey(
        'scipost.Contributor', blank=True, null=True, related_name='+')
    to_name = models.CharField(max_length=128, blank=True)
    type = models.CharField(
        max_length=16, choices=CONFLICT_OF_INTEREST_TYPES, default=TYPE_OTHER)

    # Meta
    conflict_url = models.URLField(blank=True)
    conflict_title = models.CharField(max_length=256, blank=True)
    related_submissions = models.ManyToManyField(
        'submissions.Submission', blank=True, related_name='conflicts')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        _str = '{} {}'.format(self.get_type_display(), self.origin)
        if self.conflict_title:
            _str += ' on {}...'.format(self.conflict_title[:20])
        return _str

    def clean(self):
        """Check if Conflict of Interest is complete."""
        if not self.to_contributor and not self.to_unregistered:
            raise ValidationError(
                'Conflict of Interest must be related to Contributor or UnregisteredAuthor.')
