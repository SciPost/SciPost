from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from .constants import PRODUCTION_STREAM_STATUS, PRODUCTION_STREAM_ONGOING, PRODUCTION_EVENTS
from .managers import ProductionStreamQuerySet, ProductionEventManager


class ProductionUser(models.Model):
    """
    Production Officers will have a ProductionUser object related to their account
    to relate all production related actions to.
    """
    user = models.OneToOneField(User, on_delete=models.PROTECT, unique=True,
                                related_name='production_user')

    # objects = ProductionUserQuerySet.as_manager()  -- Not implemented yet

    def __str__(self):
        return '%s, %s' % (self.user.last_name, self.user.first_name)


class ProductionStream(models.Model):
    submission = models.OneToOneField('submissions.Submission', on_delete=models.CASCADE)
    opened = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=32,
                              choices=PRODUCTION_STREAM_STATUS, default=PRODUCTION_STREAM_ONGOING)
    officer = models.ForeignKey('production.ProductionUser', blank=True, null=True,
                                related_name='streams')
    supervisor = models.ForeignKey('production.ProductionUser', blank=True, null=True,
                                   related_name='supervised_streams')

    objects = ProductionStreamQuerySet.as_manager()

    class Meta:
        permissions = (
            ('can_work_for_stream', 'Can work for stream'),
            # ('can_perform_supervisory_actions', 'Can perform supervisory actions'),
        )

    def __str__(self):
        return '{arxiv}, {title}'.format(arxiv=self.submission.arxiv_identifier_w_vn_nr,
                                         title=self.submission.title)

    def get_absolute_url(self):
        if self.status == PRODUCTION_STREAM_ONGOING:
            return reverse('production:production') + '#stream_' + str(self.id)
        return reverse('production:completed') + '#stream_' + str(self.id)

    def total_duration(self):
        totdur = self.events.aggregate(models.Sum('duration'))
        return totdur['duration__sum']


class ProductionEvent(models.Model):
    stream = models.ForeignKey(ProductionStream, on_delete=models.CASCADE, related_name='events')
    event = models.CharField(max_length=64, choices=PRODUCTION_EVENTS)
    comments = models.TextField(blank=True, null=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey('production.ProductionUser', on_delete=models.CASCADE,
                                 related_name='events')
    duration = models.DurationField(blank=True, null=True)

    objects = ProductionEventManager()

    class Meta:
        ordering = ['noted_on']

    def __str__(self):
        return '%s: %s' % (self.stream, self.get_event_display())

    def get_absolute_url(self):
        return self.stream.get_absolute_url()
