__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from collections import OrderedDict
import datetime

from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils.html import format_html

from ..constants import (
    SUBSIDY_TYPES,
    SUBSIDY_TYPE_SPONSORSHIPAGREEMENT,
    SUBSIDY_STATUS,
    SUBSIDY_WITHDRAWN,
)
from ..managers import SubsidyQuerySet, PubFracQuerySet


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
    or (e.g. for Sponsorship Agreements) the date at which the agreement enters into
    force. The date_until field is optional, and represents (where applicable) the date
    after which the object of the Subsidy is officially terminated.
    """

    organization = models.ForeignKey["Organization"](
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
            return (
                f"{self.date_from}{f' - {self.date_until}' if self.date_until else ''}: "
                f"€{self.amount} from {self.organization}"
            )
        return (
            f"{self.date_from}{f' - {self.date_until}' if self.date_until else ''}: "
            f"from {self.organization}"
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

    def compensate(self, pubfracs: PubFracQuerySet):
        """
        Allocate subsidy to uncompensated pubfracs in queryset, up to depletion.
        """
        for pubfrac in pubfracs.uncompensated():
            if pubfrac.cf_value <= self.remainder:
                pubfrac.compensated_by = self
                pubfrac.save()

    def compensate_own_pubfracs(self):
        """
        Compensate PubFracs with direct affiliation to Subsidy-giver.
        """
        max_year = self.date_until.year if self.date_until else self.date_from.year
        pubfracs = self.organization.pubfracs.filter(
            publication__publication_date__year__gte=self.date_from.year,
            publication__publication_date__year__lte=max_year,
        )
        self.compensate(pubfracs)

    def compensate_children_pubfracs(self):
        """
        Compensate PubFracs with direct affiliation to Subsidy-giver's children Organizations.
        """
        max_year = self.date_until.year if self.date_until else self.date_from.year
        for child in self.organization.children.all():
            pubfracs = child.pubfracs.filter(
                publication__publication_date__year__gte=self.date_from.year,
                publication__publication_date__year__lte=max_year,
            )
            self.compensate(pubfracs)

    @property
    def total_compensations(self):
        """
        Sum of the amounts of all compensations related to this Subsidy.
        """
        return (
            self.compensated_pubfracs.aggregate(Sum("cf_value"))["cf_value__sum"]
            if self.compensated_pubfracs.exists()
            else 0
        )

    @property
    def remainder(self):
        """
        Part of the Subsidy amount which hasn't been allocated.
        """
        return self.amount - self.total_compensations

    @property
    def compensated_pubfracs_dict(self):
        """A dict containing digested info on compensated PubFracs."""
        compensated = OrderedDict.fromkeys(
            [pf.publication.doi_label for pf in self.compensated_pubfracs.all()]
        )
        for pubfrac in self.compensated_pubfracs.all():
            compensated[pubfrac.publication.doi_label] = {"fraction": 0, "value": 0}
        for pubfrac in self.compensated_pubfracs.all():
            compensated[pubfrac.publication.doi_label]["fraction"] += pubfrac.fraction
            compensated[pubfrac.publication.doi_label]["value"] += pubfrac.cf_value
        return compensated
