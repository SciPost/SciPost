from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import reverse

from mailchimp3 import MailChimp

from .constants import MAIL_LIST_STATUSES, MAIL_LIST_STATUS_ACTIVE,\
                       MAILCHIMP_STATUSES, MAILCHIMP_SUBSCRIBED
from .managers import MailListManager

from scipost.behaviors import TimeStampedModel


class MailchimpList(TimeStampedModel):
    """
    This model is a copy of the current lists in the Mailchimp account.
    It will be used to map the Contributor's preferences to the Mailchimp's lists
    and keeping both up to date.
    """
    name = models.CharField(max_length=255)
    internal_name = models.CharField(max_length=255, blank=True)
    supporting_text = models.TextField(blank=True)
    mailchimp_list_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=255, choices=MAIL_LIST_STATUSES,
                              default=MAIL_LIST_STATUS_ACTIVE)
    open_for_subscription = models.BooleanField(default=False)
    allowed_groups = models.ManyToManyField(Group, related_name='allowed_mailchimp_lists')

    objects = MailListManager()

    class Meta:
        ordering = ['status', 'internal_name', 'name']

    def __str__(self):
        if self.internal_name:
            return self.internal_name
        return self.name

    def get_absolute_url(self):
        return reverse('mailing_lists:list_detail', args=[self.mailchimp_list_id])

    def update_membership(self, contributors, status='subscribed'):
        client = MailChimp(settings.MAILCHIMP_API_USER, settings.MAILCHIMP_API_KEY)
        for contributor in contributors:
            if self.allowed_groups.filter(user__contributor=contributor).exists():
                payload = {
                    'email_address': contributor.user.email,
                    'status': status,
                    'status_if_new': status,
                    'merge_fields': {
                        'FNAME': contributor.user.first_name,
                        'LNAME': contributor.user.last_name,
                    },
                }
                client.lists.members.create_or_update(self.mailchimp_list_id,
                                                      payload['email_address'],
                                                      payload)
        return True


class MailchimpSubscription(TimeStampedModel):
    """
    Track the Contributors' settings on wheter he/she wants to have an
    active subscription to a specific (public) list.
    """
    active_list = models.ForeignKey('mailing_lists.MailchimpList')
    contributor = models.ForeignKey('scipost.Contributor', related_name='mail_subscription')
    status = models.CharField(max_length=255, choices=MAILCHIMP_STATUSES,
                              default=MAILCHIMP_SUBSCRIBED)

    class Meta:
        unique_together = ('active_list', 'contributor',)
