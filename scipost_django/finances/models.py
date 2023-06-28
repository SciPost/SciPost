__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import os

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .constants import SUBSIDY_TYPES, SUBSIDY_TYPE_SPONSORSHIPAGREEMENT, SUBSIDY_STATUS
from .managers import SubsidyQuerySet, SubsidyPaymentQuerySet, SubsidyAttachmentQuerySet
from .utils import id_to_slug

from scipost.storage import SecureFileStorage


class Subsidy(models.Model):
    """
    A subsidy given to SciPost by an Organization.
    Any fund given to SciPost, in any form, must be associated
    to a corresponding Subsidy instance.

    This can for example be:

    * a Sponsorship agreement
    * an incidental grant
    * a development grant for a specific purpose
    * a Collaboration Agreement
    * a donation

    The date_from field represents the date at which the Subsidy was formally agreed,
    or (e.g. for Sponsorship Agreements) the date at which the agreement enters into force.
    The date_until field is optional, and represents (where applicable) the date
    after which the object of the Subsidy is officially terminated.
    """

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    subsidy_type = models.CharField(max_length=256, choices=SUBSIDY_TYPES)
    description = models.TextField()
    amount = models.PositiveIntegerField(help_text="in &euro; (rounded)")
    amount_publicly_shown = models.BooleanField(default=True)
    status = models.CharField(max_length=32, choices=SUBSIDY_STATUS)
    paid_on = models.DateField(blank=True, null=True)
    date_from = models.DateField()
    date_until = models.DateField(blank=True, null=True)
    renewable = models.BooleanField(null=True)
    renewal_of = models.ManyToManyField(
        "self", related_name="renewed_by", symmetrical=False, blank=True
    )

    objects = SubsidyQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "subsidies"
        ordering = ["-date_from"]

    def __str__(self):
        if self.amount_publicly_shown:
            return format_html(
                "{}: &euro;{} from {}, for {}",
                self.date_from,
                self.amount,
                self.organization,
                self.description,
            )
        return format_html(
            "{}: from {}, for {}", self.date_from, self.organization, self.description
        )

    def get_absolute_url(self):
        return reverse("finances:subsidy_details", args=(self.id,))

    def value_in_year(self, year):
        """
        Normalize the value of the subsidy per year.
        """
        if self.date_until is None:
            if self.date_from.year == year:
                return self.amount
            return 0
        if self.date_from.year <= year and self.date_until.year >= year:
            # keep it simple: for all years covered, spread evenly
            nr_years_covered = self.date_until.year - self.date_from.year + 1
            return int(self.amount / nr_years_covered)
        return 0

    @property
    def renewal_action_date(self):
        if self.date_until and self.subsidy_type == SUBSIDY_TYPE_SPONSORSHIPAGREEMENT:
            return self.date_until - datetime.timedelta(days=122)
        return "-"

    @property
    def renewal_action_date_color_class(self):
        if self.date_until and self.renewable:
            if self.renewed_by.exists():
                return "transparent"
            today = datetime.date.today()
            if self.date_until < today + datetime.timedelta(days=122):
                return "danger"
            elif self.date_until < today + datetime.timedelta(days=153):
                return "warning"
            return "success"
        return "transparent"

    @property
    def date_until_color_class(self):
        if self.date_until and self.renewable:
            if self.renewed_by.exists():
                return "transparent"
            today = datetime.date.today()
            if self.date_until < today:
                return "warning"
            else:
                return "success"
        return "transparent"

    @property
    def payments_all_scheduled(self):
        """
        Verify that there exist SubsidyPayment objects covering full amount.
        """
        return self.amount == self.payments.aggregate(Sum("amount"))["amount__sum"]


class SubsidyPayment(models.Model):
    subsidy = models.ForeignKey(
        "finances.Subsidy",
        related_name="payments",
        on_delete=models.CASCADE,
    )
    reference = models.CharField(max_length=64, unique=True)
    amount = models.PositiveIntegerField(help_text="in &euro;")
    date_scheduled = models.DateField()
    invoice = models.OneToOneField(
        "finances.SubsidyAttachment",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="invoice_for",
    )
    proof_of_payment = models.OneToOneField(
        "finances.SubsidyAttachment",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="proof_of_payment_for"
    )

    objects = SubsidyPaymentQuerySet.as_manager()

    def __str__(self):
        return f"payment {self.reference} for {self.subsidy}"

    @property
    def status(self):
        if self.paid:
            return "paid"
        if self.invoiced:
            return "invoiced"
        return "scheduled"

    @property
    def invoiced(self):
        return self.invoice is not None

    @property
    def invoice_date(self):
        return self.invoice.date if self.invoice else None

    @property
    def paid(self):
        return self.proof_of_payment is not None

    @property
    def payment_date(self):
        return self.proof_of_payment.date if self.proof_of_payment else None


def subsidy_attachment_path(instance, filename):
    """
    Save the uploaded SubsidyAttachments to country-specific folders.
    """
    return "uploads/finances/subsidies/{0}/{1}/{2}".format(
        instance.subsidy.date_from.strftime("%Y"),
        instance.subsidy.organization.country,
        filename,
    )


class SubsidyAttachment(models.Model):
    """
    A document related to a Subsidy.
    """

    KIND_AGREEMENT = "agreement"
    KIND_INVOICE = "invoice"
    KIND_PROOF_OF_PAYMENT = "proofofpayment"
    KIND_OTHER = "other"
    KIND_CHOICES = (
        (KIND_AGREEMENT, "Agreement"),
        (KIND_INVOICE, "Invoice"),
        (KIND_PROOF_OF_PAYMENT, "Proof of payment"),
        (KIND_OTHER, "Other"),
    )

    VISIBILITY_PUBLIC = "public"
    VISIBILITY_INTERNAL = "internal"
    VISIBILITY_FINADMINONLY = "finadminonly"
    VISIBILITY_CHOICES = (
        (VISIBILITY_PUBLIC, "Publicly visible"),
        (VISIBILITY_INTERNAL, "Internal (admin, Org Contacts)"),
        (VISIBILITY_FINADMINONLY, "SciPost FinAdmin only"),
    )

    subsidy = models.ForeignKey(
        "finances.Subsidy",
        related_name="attachments",
        blank=True,
        on_delete=models.CASCADE,
    )

    attachment = models.FileField(
        upload_to=subsidy_attachment_path, storage=SecureFileStorage()
    )

    kind = models.CharField(
        max_length=32,
        choices=KIND_CHOICES,
        default=KIND_AGREEMENT,
    )

    date = models.DateField(blank=True, null=True)

    description = models.TextField(blank=True)

    visibility = models.CharField(
        max_length=32,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_FINADMINONLY,
    )

    objects = SubsidyAttachmentQuerySet.as_manager()

    def __str__(self):
        return "%s, attachment to %s" % (self.attachment.name, self.subsidy)

    def get_absolute_url(self):
        if self.subsidy:
            return reverse(
                "finances:subsidy_attachment", args=(self.subsidy.id, self.id)
            )

    @property
    def filename(self):
        return os.path.basename(self.attachment.name)

    @property
    def publicly_visible(self):
        return self.visibility == self.VISIBILITY_PUBLIC

    def visible_to_user(self, current_user):
        if self.publicly_visible or current_user.has_perm(
            "scipost.can_manage_subsidies"
        ):
            return True
        if self.subsidy.organization.contactrole_set.filter(
            contact__user=current_user
        ).exists():
            return True
        return False


###########################
# Work hours registration #
###########################


class WorkLog(models.Model):
    HOURLY_RATE = 22.0
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comments = models.TextField(blank=True)
    log_type = models.CharField(max_length=128, blank=True)
    duration = models.DurationField(blank=True, null=True)
    work_date = models.DateField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content = GenericForeignKey()

    class Meta:
        default_related_name = "work_logs"
        ordering = ["-work_date", "created"]

    def __str__(self):
        return "Log of {0} {1} on {2}".format(
            self.user.first_name, self.user.last_name, self.work_date
        )

    @property
    def slug(self):
        return id_to_slug(self.id)


####################
# Periodic Reports #
####################


class PeriodicReportType(models.Model):
    name = models.CharField(max_length=256)
    description = models.TextField()

    def __str__(self):
        return self.name


def periodic_report_upload_path(instance, filename):
    return f"uploads/finances/periodic_reports/{instance.for_year}/{filename}"


class PeriodicReport(models.Model):
    """
    Any form of report (annual, financial, administrative etc).
    """
    _type = models.ForeignKey(
        'finances.PeriodicReportType',
        on_delete=models.CASCADE,
    )
    _file = models.FileField(
        upload_to=periodic_report_upload_path,
        max_length=256,
    )
    created_on = models.DateTimeField(default=timezone.now)
    for_year = models.PositiveSmallIntegerField()

    class META:
        ordering = ["-for_year", "_type__name"]

    def __str__(self):
        return f"{self.for_year} {self._type}"

    def get_absolute_url(self):
        if self._file:
            return reverse("finances:periodicreport_file", kwargs={"pk": self.id})
