from django.db import models
from django.utils import timezone

from .constants import PRODUCTION_STREAM_STATUS, PRODUCTION_STREAM_ONGOING, PRODUCTION_EVENTS
from .managers import ProductionStreamManager

from scipost.models import Contributor


##############
# Production #
##############

class ProductionStream(models.Model):
    submission = models.OneToOneField('submissions.Submission', on_delete=models.CASCADE)
    opened = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=32,
                              choices=PRODUCTION_STREAM_STATUS, default=PRODUCTION_STREAM_ONGOING)

    objects = ProductionStreamManager()

    def __str__(self):
        return str(self.submission)

    def total_duration(self):
        totdur = self.productionevent_set.aggregate(models.Sum('duration'))
        return totdur['duration__sum']


class ProductionEvent(models.Model):
    stream = models.ForeignKey(ProductionStream, on_delete=models.CASCADE)
    event = models.CharField(max_length=64, choices=PRODUCTION_EVENTS)
    comments = models.TextField(blank=True, null=True)
    noted_on = models.DateTimeField(auto_now_add=True)
    noted_by = models.ForeignKey(Contributor, on_delete=models.CASCADE)
    duration = models.DurationField(blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (str(self.stream.submission), self.get_event_display())
