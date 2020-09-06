__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.db import models
from django.urls import reverse

from ..managers import FellowQuerySet

from scipost.behaviors import TimeStampedModel
from scipost.models import get_sentinel_user


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
