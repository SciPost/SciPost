from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.functional import cached_property

from .constants import PRODUCTION_STREAM_STATUS, PRODUCTION_STREAM_INITIATED, PRODUCTION_EVENTS,\
                       EVENT_MESSAGE, EVENT_HOUR_REGISTRATION, PRODUCTION_STREAM_COMPLETED,\
                       PROOF_STATUSES, PROOF_UPLOADED
from .managers import ProductionStreamQuerySet, ProductionEventManager, ProofsQuerySet
from .utils import proof_id_to_slug

from scipost.storage import SecureFileStorage


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
    submission = models.OneToOneField('submissions.Submission', on_delete=models.CASCADE,
                                      related_name='production_stream')
    opened = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=32, choices=PRODUCTION_STREAM_STATUS,
                              default=PRODUCTION_STREAM_INITIATED)

    officer = models.ForeignKey('production.ProductionUser', blank=True, null=True,
                                related_name='streams')
    supervisor = models.ForeignKey('production.ProductionUser', blank=True, null=True,
                                   related_name='supervised_streams')

    objects = ProductionStreamQuerySet.as_manager()

    class Meta:
        permissions = (
            ('can_work_for_stream', 'Can work for stream'),
            ('can_perform_supervisory_actions', 'Can perform supervisory actions'),
        )

    def __str__(self):
        return '{arxiv}, {title}'.format(arxiv=self.submission.arxiv_identifier_w_vn_nr,
                                         title=self.submission.title)

    def get_absolute_url(self):
        return reverse('production:stream', args=(self.id,))

    @cached_property
    def total_duration(self):
        totdur = self.events.aggregate(models.Sum('duration'))
        return totdur['duration__sum']

    @cached_property
    def completed(self):
        return self.status == PRODUCTION_STREAM_COMPLETED


class ProductionEvent(models.Model):
    stream = models.ForeignKey(ProductionStream, on_delete=models.CASCADE, related_name='events')
    event = models.CharField(max_length=64, choices=PRODUCTION_EVENTS, default=EVENT_MESSAGE)
    comments = models.TextField(blank=True, null=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey('production.ProductionUser', on_delete=models.CASCADE,
                                 related_name='events')
    noted_to = models.ForeignKey('production.ProductionUser', on_delete=models.CASCADE,
                                 blank=True, null=True, related_name='received_events')
    duration = models.DurationField(blank=True, null=True)

    objects = ProductionEventManager()

    class Meta:
        ordering = ['noted_on']

    def __str__(self):
        return '%s: %s' % (self.stream, self.get_event_display())

    def get_absolute_url(self):
        return self.stream.get_absolute_url()

    @cached_property
    def editable(self):
        return self.event in [EVENT_MESSAGE, EVENT_HOUR_REGISTRATION] and not self.stream.completed


def proofs_upload_location(instance, filename):
    submission = instance.stream.submission
    return 'UPLOADS/PROOFS/{year}/{arxiv}/{filename}'.format(
        year=submission.submission_date.year,
        arxiv=submission.arxiv_identifier_wo_vn_nr,
        filename=filename)


class Proof(models.Model):
    """
    A Proof directly related to a ProductionStream and Submission in SciPost.
    It's meant to help the Production team
    """
    attachment = models.FileField(upload_to=proofs_upload_location, storage=SecureFileStorage())
    version = models.PositiveSmallIntegerField(default=0)
    stream = models.ForeignKey('production.ProductionStream', related_name='proofs')
    uploaded_by = models.ForeignKey('production.ProductionUser', related_name='+')
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=PROOF_STATUSES, default=PROOF_UPLOADED)
    accessible_for_authors = models.BooleanField(default=False)

    objects = ProofsQuerySet.as_manager()

    class Meta:
        ordering = ['stream', 'version']

    def get_absolute_url(self):
        return reverse('production:proof_pdf', kwargs={'slug': self.slug})

    def __str__(self):
        return 'Proof {version} for Stream {stream}'.format(
            version=self.version, stream=self.stream.submission.title)

    def save(self, *args, **kwargs):
        # Control Report count per Submission.
        if not self.version:
            self.version = self.stream.proofs.count() + 1
        return super().save(*args, **kwargs)

    @property
    def slug(self):
        return proof_id_to_slug(self.id)
