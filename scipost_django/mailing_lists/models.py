__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json
import os
import re

from django.conf.urls import static
from django.core.mail import EmailMultiAlternatives
from django.db import models, transaction
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from django.urls import reverse

from django.utils.html import strip_tags
from mailchimp3 import MailChimp

from common.utils.models import get_current_domain
from mails.models import MAIL_RENDERED, MailLog

from .constants import (
    MAIL_LIST_STATUSES,
    MAIL_LIST_STATUS_ACTIVE,
    MAILCHIMP_STATUSES,
    MAILCHIMP_SUBSCRIBED,
)
from .managers import MailListManager

from profiles.models import Profile, ProfileEmail
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
        return reverse(
            "mailing_lists:mailchimp_list_detail",
            args=[self.mailchimp_list_id],
        )

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
            accepts_SciPost_emails=True,
            contributor__dbuser__email__in=unsubscribe_emails,
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


class MailingList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    is_opt_in = models.BooleanField(default=False)
    eligible_subscribers = models.ManyToManyField(
        Contributor,
        blank=True,
        related_name="eligible_mailing_lists",
    )
    subscribed = models.ManyToManyField(
        Contributor,
        blank=True,
        related_name="subscribed_mailing_lists",
    )

    @property
    def email_list(self):
        """
        Returns a list of email addresses of all Contributors that are subscribed to this list.
        """
        return list(
            self.subscribed.annotate(
                primary_email=models.Subquery(
                    ProfileEmail.objects.filter(
                        profile=models.OuterRef("profile"), primary=True
                    ).values("email")[:1]
                )
            ).values_list("primary_email", flat=True)
        )

    @property
    def latest_newsletter(self):
        """
        Returns the latest newsletter sent to this list.
        """
        return (
            self.newsletters.filter(status=Newsletter.STATUS_SENT)
            .order_by("-sent_on")
            .first()
        )

    def add_eligible_subscriber(self, contributor):
        """Adds the contributor to the list of eligible subscribers."""
        self.eligible_subscribers.add(contributor)
        # If the list is not opt-in, automatically subscribe the contributor
        if not self.is_opt_in:
            self.subscribe(contributor)

    def subscribe(self, contributor):
        """Subscribes the contributor to the list."""
        if contributor not in self.eligible_subscribers.all():
            raise ValueError("Contributor is not eligible to subscribe to this list.")
        self.subscribed.add(contributor)

    def unsubscribe(self, contributor):
        """Unsubscribes the contributor from the list."""
        if contributor not in self.subscribed.all():
            raise ValueError("Contributor is not subscribed to this list.")
        self.subscribed.remove(contributor)

    def __str__(self):
        return self.name


class Newsletter(models.Model):
    """
    A hand-written periodical email that is sent to all subscribers of a mailing list.
    """

    STATUS_DRAFT = "draft"
    STATUS_SCHEDULED = "scheduled"
    STATUS_SENT = "sent"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_SENT, "Sent"),
    ]

    mailing_list = models.ForeignKey(
        MailingList,
        on_delete=models.CASCADE,
        related_name="newsletters",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    sent_on = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.mailing_list is not None:
            return f"{self.title} to {self.mailing_list.name}"
        else:
            return f"{self.title} (no mailing list)"

    @property
    def email_content(self):
        """
        Return full HTML content of the email including the header, footer and styling.
        """

        # Load css content
        css_path = os.path.join(
            settings.BASE_DIR, "scipost/static/scipost/assets/css/newsletter.css"
        )
        css_content = re.sub(r"\s+", " ", open(css_path, "r").read())
        domain = get_current_domain()
        return render_to_string(
            "mailing_lists/newsletter_email.html",
            {
                "newsletter": self,
                "css_content": css_content,
                "domain": domain,
            },
        )

    def send(self):
        """
        Creates the mailing task(s) to send the newsletter.
        """
        # Remove the style tags from the email content and strip the tags
        stripped_email_content = re.sub(r"<style>.+?</style>", "", self.email_content)
        stripped_email_content = strip_tags(stripped_email_content).strip()
        stripped_email_content = re.sub(r" +", " ", stripped_email_content)
        stripped_email_content = re.sub(
            r"(\r?\s?\n\s?\r?){2,}", "\n\n", stripped_email_content
        )

        # Create a bulk MailLog item which the cronjob will pick up
        mail_log = MailLog.objects.create(
            type=MailLog.TYPE_BULK,
            status=MAIL_RENDERED,
            from_email="SciPost <noreply@scipost.org>",
            subject=f"[SciPost] {self.mailing_list.name}: {self.title}",
            body=stripped_email_content,
            body_html=self.email_content,
            to_recipients=self.mailing_list.email_list,
        )
        self.sent_on = mail_log.created
        self.status = Newsletter.STATUS_SENT
        self.save()

    def get_media_folder(self):
        """
        Returns the folder where the media for this newsletter is stored.
        """
        return f"newsletters/{self.pk}/media"

    @property
    def media(self):
        """
        Returns the media files that are associated with this newsletter.
        """
        media_folder = settings.MEDIA_ROOT + self.get_media_folder()
        if not os.path.exists(media_folder):
            os.makedirs(media_folder)

        media_file_paths = [
            f"{self.get_media_folder()}/{media}"
            for media in os.listdir(settings.MEDIA_ROOT + self.get_media_folder())
        ]

        media_site_path = settings.MEDIA_URL + self.get_media_folder() + "/"
        media = [
            {
                "name": os.path.basename(media_file),
                "path": media_site_path + os.path.basename(media_file),
            }
            for media_file in media_file_paths
        ]
        return media
