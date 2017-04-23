from django.db import models
from django.contrib.auth.models import Group

from .constants import MAIL_LIST_STATUSES, MAIL_LIST_STATUS_ACTIVE

from scipost.behaviors import TimeStampedModel


class ActiveMailchimpList(TimeStampedModel):
    """
    This model is a copy of the current lists in the Mailchimp account.
    It will be used to map the Contributor's preferences to the Mailchimp's lists
    and keeping both up to date.
    """
    name = models.CharField(max_length=255)
    mailchimp_list_id = models.CharField(max_length=255)
    status = models.CharField(max_length=255, choices=MAIL_LIST_STATUSES,
                              default=MAIL_LIST_STATUS_ACTIVE)
    allowed_groups = models.ManyToManyField(Group, related_name='allowed_mailchimp_lists')

    class Meta:
        default_permissions = ('delete',)

    def __str__(self):
        return self.name


class ActiveMailchimpSubscription(TimeStampedModel):
    """
    Track the Contributors' settings on wheter he/she wants to have an
    active subscription to a specific (public) list.
    """
    active_list = models.ForeignKey('mailchimp.ActiveMailchimpList')
    contributor = models.ForeignKey('scipost.Contributor')
