import datetime

from django.db import models

from scipost.behaviors import TimeStampedModel

from .managers import FellowQuerySet


class EditorialCollegeFellowship(TimeStampedModel):
    """
    Editorial College Fellowship connecting Editorial College and Contributors,
    possibly with a limiting start/until date.

    The date range will effectively be used while determining 'the pool' for a specific
    Submission, so it has a direct effect on the submission date.
    """
    contributor = models.ForeignKey('scipost.Contributor', on_delete=models.CASCADE,
                                    related_name='fellowships')
    affiliation = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(null=True, blank=True)
    until_date = models.DateField(null=True, blank=True)

    objects = FellowQuerySet.as_manager()

    class Meta:
        unique_together = ('contributor', 'start_date', 'until_date')

    def __str__(self):
        return self.contributor.__str__()

    def is_active(self):
        today = datetime.date.today()
        if not self.start_date:
            if not self.until_date:
                return True
            return today <= self.until_date
        elif not self.until_date:
            return today >= self.start_date
        return today >= self.start_date and today <= self.until_date
