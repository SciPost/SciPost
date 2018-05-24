from django.db import models

from .constants import CONFLIC_OF_INTEREST_STATUSES, STATUS_UNVERIFIED


class ConflictOfInterest(models.Model):
    """Conflict of Interest is a flagged relation between scientists."""

    status = models.CharField(
        max_length=16, choices=CONFLIC_OF_INTEREST_STATUSES, default=STATUS_UNVERIFIED)
    origin = models.ForeignKey('scipost.Contributor')
    to_contributor = models.ForeignKey('scipost.Contributor', blank=True, null=True)
    to_unregistered = models.ForeignKey('journals.UnregisteredAuthor', blank=True, null=True)

    def clean(self):
        if not self.to_contributor and not self.to_unregistered:
            raise NotImplementedError('Choose something...')
        raise NotImplementedError('Fine.')
