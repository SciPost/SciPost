__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .constants import SUBSIDY_TYPES, SUBSIDY_TYPE_SPONSORSHIPAGREEMENT, SUBSIDY_STATUS
from .utils import id_to_slug

from scipost.storage import SecureFileStorage


class Subsidy(models.Model):
    """
    A subsidy given to SciPost by an Organization.
    Any fund given to SciPost, in any form, must be associated
    to a corresponding Subsidy instance.

    This can for example be:
    - a Sponsorship agreement
    - an incidental grant
    - a development grant for a specific purpose
    - a Collaboration Agreement
    - a donation

    The date field represents the date at which the Subsidy was formally agreed,
    or (e.g. for Sponsorship Agreements) the date at which the agreement enters into force.
    The date_until field is optional, and represents (where applicable) the date
    after which the object of the Subsidy is officially terminated.
    """
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    subsidy_type = models.CharField(max_length=256, choices=SUBSIDY_TYPES)
    description = models.TextField()
    amount = models.PositiveIntegerField(help_text="in &euro; (rounded)")
    amount_publicly_shown = models.BooleanField(default=True)
    status = models.CharField(max_length=32, choices=SUBSIDY_STATUS)
    date = models.DateField()
    date_until = models.DateField(blank=True, null=True)
    renewable = models.NullBooleanField()
    renewal_of = models.ManyToManyField('self', related_name='renewed_by',
                                        symmetrical=False, blank=True)

    class Meta:
        verbose_name_plural = 'subsidies'
        ordering = ['-date']

    def __str__(self):
        return format_html('{}: &euro;{} from {}, for {}',
                           self.date, self.amount, self.organization, self.description)

    def get_absolute_url(self):
        return reverse('finances:subsidy_details', args=(self.id,))

    @property
    def renewal_action_date(self):
        if self.date_until and self.subsidy_type == SUBSIDY_TYPE_SPONSORSHIPAGREEMENT:
            return self.date_until - datetime.timedelta(days=122)
        return '-'

    @property
    def renewal_action_date_color_class(self):
        if self.date_until and self.renewable:
            if self.renewed_by.exists():
                return 'transparent'
            today = datetime.date.today()
            if self.date_until < today + datetime.timedelta(days=122):
                return 'danger'
            elif self.date_until < today + datetime.timedelta(days=153):
                return 'warning'
            return 'success'
        return 'transparent'

    @property
    def date_until_color_class(self):
        if self.date_until and self.renewable:
            if self.renewed_by.exists():
                return 'transparent'
            today = datetime.date.today()
            if self.date_until < today:
                return 'warning'
            else:
                return 'success'
        return 'transparent'


def subsidy_attachment_path(instance, filename):
    """
    Save the uploaded SubsidyAttachments to country-specific folders.
    """
    return 'uploads/finances/subsidies/{0}/{1}/{2}'.format(
        instance.subsidy.date.strftime('%Y'),
        instance.subsidy.organization.country, filename)

class SubsidyAttachment(models.Model):
    """
    A document related to a Subsidy.
    """
    attachment = models.FileField(upload_to=subsidy_attachment_path,
                                  storage=SecureFileStorage())
    name = models.CharField(max_length=128)
    subsidy = models.ForeignKey('finances.Subsidy', related_name='attachments',
                                blank=True, on_delete=models.CASCADE)
    publicly_visible = models.BooleanField(default=False)

    def __str__(self):
        return '%s, attachment to %s' % (self.name, self.subsidy)

    def get_absolute_url(self):
        if self.subsidy:
            return reverse('finances:subsidy_attachment', args=(self.subsidy.id, self.id))

    def visible_to_user(self, current_user):
        if self.publicly_visible or current_user.has_perm('scipost.can_manage_subsidies'):
            return True
        if self.subsidy.organization.contactrole_set.filter(contact__user=current_user).exists():
            return True
        return False


###########################
# Work hours registration #
###########################


class WorkLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comments = models.TextField(blank=True)
    log_type = models.CharField(max_length=128, blank=True)
    duration = models.DurationField(blank=True, null=True)
    work_date = models.DateField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                     on_delete=models.CASCADE)
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
