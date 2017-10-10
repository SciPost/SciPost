from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils import timezone

from .utils import id_to_slug


class WorkLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    comments = models.TextField(blank=True)
    log_type = models.CharField(max_length=128, blank=True)
    duration = models.DurationField(blank=True, null=True)
    work_date = models.DateField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content = GenericForeignKey()

    class Meta:
        default_related_name = 'work_logs'
        ordering = ['-work_date', 'created']

    def __str__(self):
        return 'Log of {0} {1} on {2}'.format(
            self.user.first_name, self.user.last_name, self.work_date)

    @property
    def slug(self):
        return id_to_slug(self.id)
