__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .constants import SUBSIDY_TYPES, SUBSIDY_STATUS, SUBSIDY_DURATION
from .utils import id_to_slug


class Subsidy(models.Model):
    """
    A subsidy given to SciPost by an Organization.
    Any fund given to SciPost, in any form, must be associated
    to a corresponding Subsidy instance.

    This can for example be:
    - a Partners agreement
    - an incidental grant
    - a development grant for a specific purpose
    - a Collaboration Agreement
    - a donation
    """
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    subsidy_type = models.CharField(max_length=256, choices=SUBSIDY_TYPES)
    description = models.CharField(max_length=256)
    amount = models.PositiveSmallIntegerField(help_text="in &euro; (rounded)")
    status = models.CharField(max_length=32, choices=SUBSIDY_STATUS)
    date = models.DateField()
    duration = models.DurationField(choices=SUBSIDY_DURATION, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'subsidies'

    def __str__(self):
        return format_html('{}: &euro;{} from {}, for {}',
                           self.date, self.amount, self.organization, self.description)

    def get_absolute_url(self):
        return reverse('finances:subsidy_details', args=(self.id,))


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
