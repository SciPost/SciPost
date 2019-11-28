__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models


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
    description = models.TextField()
    application_deadline = models.DateField()
    status = models.CharField(max_length=10, choices=JOBOPENING_STATUSES)

    class Meta:
        ordering = ['-announced']

    def __str__(self):
        return '%s (%s)' % (self.title, self.slug)
