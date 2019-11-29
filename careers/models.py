__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.urls import reverse

from .managers import JobOpeningQuerySet


class JobOpening(models.Model):
    """
    Information on a job opening.
    """
    DRAFTED = 'drafted'
    VISIBLE = 'visible'
    CLOSED = 'closed'
    JOBOPENING_STATUSES = (
        (DRAFTED, 'Drafted (not publicly visible)'),
        (VISIBLE, 'Publicly visible'),
        (CLOSED, 'Closed')
    )
    slug = models.SlugField()
    announced = models.DateField()
    title = models.CharField(max_length=128)
    short_description = models.TextField()
    description = models.TextField()
    application_deadline = models.DateField()
    status = models.CharField(max_length=10, choices=JOBOPENING_STATUSES)

    objects = JobOpeningQuerySet.as_manager()

    class Meta:
        ordering = ['-announced']

    def __str__(self):
        return '%s (%s)' % (self.title, self.slug)

    def get_absolute_url(self):
        return reverse('careers:jobopening_detail', kwargs={'slug': self.slug})
