__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField

from .managers import MailLogQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from organizations.models import Organization
    from profiles.models import ProfileEmail


MAIL_NOT_RENDERED, MAIL_RENDERED = "not_rendered", "rendered"
MAIL_SENT = "sent"
MAIL_STATUSES = (
    (MAIL_NOT_RENDERED, "Not rendered"),
    (MAIL_RENDERED, "Rendered"),
    (MAIL_SENT, "Sent"),
)


class MailLog(models.Model):
    """
    The MailLog table is meant as a container of mails.
    Mails are not directly sent, but added to this table first.
    Using a cronjob, the unsent messages are eventually sent using
    the chosen MailBackend.

    A mail can be of two types:
    - Single: This log entry represents a single mail (optionally with multiple recipients)
    - Bulk: This log entry represents an array of (identical) mails,
            each with a single recipient, e.g. announcements or newsletters.
    """

    TYPE_SINGLE = "single"
    TYPE_BULK = "bulk"
    TYPE_CHOICES = (
        (TYPE_SINGLE, "Single"),
        (TYPE_BULK, "Bulk"),
    )

    processed = models.BooleanField(default=False)
    type = models.CharField(max_length=64, choices=TYPE_CHOICES, default=TYPE_SINGLE)
    status = models.CharField(
        max_length=16, choices=MAIL_STATUSES, default=MAIL_RENDERED
    )

    mail_code = models.CharField(max_length=254, blank=True)
    message_id = models.CharField(
        max_length=254, null=True, blank=True, help_text="The Message-ID header"
    )

    body = models.TextField()
    body_html = models.TextField(blank=True)

    to_recipients = ArrayField(models.EmailField(), blank=True, null=True)
    cc_recipients = ArrayField(models.EmailField(), blank=True, null=True)
    bcc_recipients = ArrayField(models.EmailField(), blank=True, null=True)

    sent_to = ArrayField(models.EmailField(), blank=True, null=True)

    from_email = models.CharField(max_length=254, blank=True)
    subject = models.CharField(max_length=254, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    latest_activity = models.DateTimeField(auto_now=True)

    objects = MailLogQuerySet.as_manager()

    if TYPE_CHECKING:
        context: RelatedManager["MailLogRelation"]

    class Meta:
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["message_id"],
                name="unique_message_id",
                violation_error_message="Message-ID header must be unique",
                nulls_distinct=True,
            ),
        ]

    def __str__(self):
        nr_recipients = self.get_number_of_recipients()
        if self.type == self.TYPE_SINGLE:
            recipients_str = f"{nr_recipients} recipients"
        elif self.type == self.TYPE_BULK:
            nr_sent = len(self.sent_to) if self.sent_to else 0
            recipients_str = f"{nr_sent}/{nr_recipients} recipients"

        return "{id}. {subject} ({recipients_str})".format(
            id=self.id,
            subject=self.subject[:30],
            recipients_str=recipients_str,
        )

    def get_number_of_recipients(self):
        def sum_optional(*args):
            return sum([len(arg) for arg in args if arg])

        if self.type == self.TYPE_SINGLE:
            return sum_optional(
                self.to_recipients, self.cc_recipients, self.bcc_recipients
            )
        elif self.type == self.TYPE_BULK:
            return sum_optional(self.to_recipients)
        return 0

    def get_full_context(self):
        """Get the full template context needed to render the template."""
        if hasattr(self, "_context"):
            return self._context
        self._context = {}
        for relation in self.context.all():
            self._context[relation.name] = relation.get_item()
        return self._context


class MailLogRelation(models.Model):
    """
    A template context item for the MailLog in case the a mail has delayed rendering.
    This may be plain text or any relation within the database.
    """

    mail = models.ForeignKey(
        "mails.MailLog", on_delete=models.CASCADE, related_name="context"
    )

    name = models.CharField(max_length=254)
    value = models.TextField(blank=True)

    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    def get_item(self):
        if self.value:
            return self.value
        elif self.content_object:
            return self.content_object
        return None


class MailAddressDomain(models.Model):
    """
    A model to represent the domain of an email address.
    """

    KIND_UNKNOWN = "unknown"
    KIND_PERSONAL = "personal"
    KIND_INSTITUTIONAL = "institutional"
    KIND_CHOICES = (
        (KIND_UNKNOWN, "Unknown"),
        (KIND_PERSONAL, "Personal"),
        (KIND_INSTITUTIONAL, "Institutional"),
    )

    domain = models.CharField(max_length=128, unique=True)
    kind = models.CharField(max_length=16, choices=KIND_CHOICES, default=KIND_UNKNOWN)
    organization = models.ForeignKey["Organization"](
        "organizations.Organization", blank=True, null=True, on_delete=models.CASCADE
    )
    ror_id_matches = ArrayField(models.CharField(max_length=128), blank=True, null=True)

    if TYPE_CHECKING:
        profile_emails = RelatedManager["ProfileEmail"]

    class Meta:
        ordering = ["domain"]

    def __str__(self):
        return self.domain
