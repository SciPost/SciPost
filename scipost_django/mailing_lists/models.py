__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json

from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import reverse

from mailchimp3 import MailChimp

from .constants import (
    MAIL_LIST_STATUSES,
    MAIL_LIST_STATUS_ACTIVE,
    MAILCHIMP_STATUSES,
    MAILCHIMP_SUBSCRIBED,
)
from .managers import MailListManager

from profiles.models import Profile
from scipost.behaviors import TimeStampedModel
from scipost.constants import NORMAL_CONTRIBUTOR
from scipost.models import Contributor


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
    status = models.CharField(
        max_length=255, choices=MAIL_LIST_STATUSES, default=MAIL_LIST_STATUS_ACTIVE
    )
    subscriber_count = models.PositiveIntegerField(default=0)
    open_for_subscription = models.BooleanField(default=False)
    allowed_groups = models.ManyToManyField(
        Group, related_name="allowed_mailchimp_lists"
    )

    objects = MailListManager()

    class Meta:
        ordering = ["status", "internal_name", "name"]

    def __str__(self):
        if self.internal_name:
            return self.internal_name
        return self.name

    def get_absolute_url(self):
        return reverse("mailing_lists:list_detail", args=[self.mailchimp_list_id])

    @transaction.atomic
    def update_members(self, status="subscribed"):
        """
        Update the subscribers in the MailChimp account.
        """
        # Extreme timeset value (1 minute) to allow for huge maillist subscribes
        client = MailChimp(settings.MAILCHIMP_API_USER, settings.MAILCHIMP_API_KEY)
        try:
            unsubscribe_emails = []
            # Find all campaigns on the account
            campaigns = client.campaigns.all(get_all=True)
            for campaign in campaigns["campaigns"]:
                # All unsubscriptions are registered per campaign
                # Should be improved later on
                unsubscribers = client.reports.unsubscribes.all(campaign["id"], True)
                for unsubscriber in unsubscribers["unsubscribes"]:
                    if unsubscriber["list_id"] == self.mailchimp_list_id:
                        unsubscribe_emails.append(unsubscriber["email_address"])
        except KeyError:
            # Call with MailChimp went wrong, returned invalid data
            return None

        # Unsubscribe *all* Contributors in the database if asked for
        updated_contributors = Profile.objects.filter(
            accepts_SciPost_emails=True, contributor__user__email__in=unsubscribe_emails
        ).update(accepts_SciPost_emails=False)

        # Check the current list of subscribers in MailChimp account
        subscribers_list = client.lists.members.all(
            self.mailchimp_list_id, True, fields="members.email_address"
        )
        subscribers_list = [sub["email_address"] for sub in subscribers_list["members"]]

        # Retrieve *users* that are in the right group and didn't unsubscribe and
        # are not in the list yet.
        db_subscribers = (
            User.objects.filter(contributor__isnull=False)
            .filter(is_active=True, contributor__status=NORMAL_CONTRIBUTOR)
            .filter(
                contributor__profile__accepts_SciPost_emails=True,
                groups__in=self.allowed_groups.all(),
                email__isnull=False,
                first_name__isnull=False,
                last_name__isnull=False,
            )
            .exclude(email__in=subscribers_list)
        )

        # Build batch data
        batch_data = {"operations": []}
        add_member_path = "lists/%s/members" % self.mailchimp_list_id
        for user in db_subscribers:
            batch_data["operations"].append(
                {
                    "method": "POST",
                    "path": add_member_path,
                    "body": json.dumps(
                        {
                            "status": status,
                            "status_if_new": status,
                            "email_address": user.email,
                            "merge_fields": {
                                "FNAME": user.first_name,
                                "LNAME": user.last_name,
                            },
                        }
                    ),
                }
            )
        # Make the subscribe call
        post_response = client.batches.create(data=batch_data)

        list_data = client.lists.get(list_id=self.mailchimp_list_id)
        self.subscriber_count = list_data["stats"]["member_count"]
        self.save()
        return (updated_contributors, len(db_subscribers), post_response)


class MailchimpSubscription(TimeStampedModel):
    """
    Track the Contributors' settings on wheter he/she wants to have an
    active subscription to a specific (public) list.
    """

    active_list = models.ForeignKey(
        "mailing_lists.MailchimpList", on_delete=models.CASCADE
    )
    contributor = models.ForeignKey(
        "scipost.Contributor",
        on_delete=models.CASCADE,
        related_name="mail_subscription",
    )
    status = models.CharField(
        max_length=255, choices=MAILCHIMP_STATUSES, default=MAILCHIMP_SUBSCRIBED
    )

    class Meta:
        unique_together = (
            "active_list",
            "contributor",
        )
