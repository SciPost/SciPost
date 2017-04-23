from django.db import models
from django.contrib.auth.models import Group
from django.urls import reverse

from .constants import MAIL_LIST_STATUSES, MAIL_LIST_STATUS_ACTIVE
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


class ActiveMailchimpSubscription(TimeStampedModel):
    """
    Track the Contributors' settings on wheter he/she wants to have an
    active subscription to a specific (public) list.
    """
    active_list = models.ForeignKey('mailing_lists.MailchimpList')
    contributor = models.ForeignKey('scipost.Contributor')
