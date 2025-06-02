__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from collections import OrderedDict
from itertools import groupby
import datetime

from django.db import models
from django.db.models import F, Q, QuerySet, Sum
from django.db.models.functions import ExtractYear
from django.urls import reverse

from finances.utils.compensations import CompensationStrategy
from finances.models import PubFrac
from scipost.fields import ChoiceArrayField

from ..constants import (
    SUBSIDY_RECEIVED,
    SUBSIDY_TYPES,
    SUBSIDY_TYPE_SPONSORSHIPAGREEMENT,
    SUBSIDY_STATUS,
    SUBSIDY_UPTODATE,
)
from ..managers import SubsidyQuerySet, PubFracQuerySet

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from organizations.models import Organization
    from funders.models import IndividualBudget


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
    collective = models.ForeignKey["SubsidyCollective"](
        "SubsidyCollective",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subsidies",
    )
    individual_budget = models.ForeignKey["IndividualBudget"](
        "funders.IndividualBudget",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="subsidies_funded",
    )

    compensation_strategies_keys = ChoiceArrayField(
        models.CharField(max_length=32, choices=CompensationStrategy.get_choices()),
        default=CompensationStrategy.get_default_strategies_keys_list,
    )
    compensation_strategies_details = models.JSONField(blank=True, default=dict)

    if TYPE_CHECKING:
        collectives: RelatedManager["SubsidyCollective"]
        compensated_pubfracs: RelatedManager["PubFrac"]

    objects = SubsidyQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "subsidies"
        ordering = ["-date_from"]
        get_latest_by = "date_until"

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

    @classmethod
    def compensate_pubfracs(cls, subsidies: "None | QuerySet[Subsidy]" = None):
        """
        Compute pubfrac compensations for the provided subsidies.
        If no subsidies are specified, all subsidies are considered.
        Returns the number of PubFracs updated.
        """
        if subsidies is None:
            subsidies = Subsidy.objects.all()
            PubFrac.objects.update(compensated_by=None)
        else:
            PubFrac.objects.filter(compensated_by__in=subsidies).update(
                compensated_by=None
            )
        subsidies = subsidies.filter(
            Q(status=SUBSIDY_RECEIVED) | Q(status=SUBSIDY_UPTODATE)
        )

        subsidy_pubfrac_table: list[dict[str, Any]] = []
        for subsidy in subsidies.annotate(remaining=F("amount")):
            for strategy in subsidy.compensation_strategies:
                for pubfrac in PubFrac.objects.filter(strategy.get_filter(subsidy)):
                    subsidy_pubfrac_table.append(
                        {
                            "subsidy": subsidy,
                            "pubfrac": pubfrac,
                            "priority": strategy.priority,
                        }
                    )

        subsidy_pubfrac_table.sort(
            key=lambda x: (
                x["pubfrac"].id,  # PubFrac ID for grouping later
                x["priority"],  # Priority of the compensation strategy
                x["subsidy"].date_from.year,  # Year of the subsidy
                -x["subsidy"].remaining,  # Remaining amount (descending)
            )
        )

        pubfracs_to_update: list[PubFrac] = []
        for pubfrac, group_table in groupby(
            subsidy_pubfrac_table, key=lambda x: x["pubfrac"]
        ):
            for row in group_table:
                subsidy = row["subsidy"]
                # Only if the subsidy has enough remaining amount,
                # assign it to the PubFrac and break out of the loop
                if subsidy.remaining >= pubfrac.cf_value:
                    pubfrac.compensated_by = subsidy
                    subsidy.remaining -= pubfrac.cf_value
                    pubfracs_to_update.append(pubfrac)
                    break

        return PubFrac.objects.bulk_update(pubfracs_to_update, ["compensated_by"])

    def allocate(self):
        """
        Allocate subsidy to uncompensated pubfracs up to depletion.
        """
        self.compensate_pubfracs(subsidies=Subsidy.objects.filter(id=self.id))

    @property
    def compensation_strategies(self):
        """
        Returns the compensation strategies realized from the `CompensationStrategy` enum.
        """
        return [
            CompensationStrategy.from_key(key)
            for key in self.compensation_strategies_keys
        ]

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


class SubsidyCollective(models.Model):
    """
    A collective of Subsidies, which can be used to group together relevant subsidies.
    Primarily used to group together all subsidies from a single collective agreement,
    as coordinated by a "parent" Organization.
    """

    coordinator = models.ForeignKey["Organization"](
        "organizations.Organization", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=256, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    if TYPE_CHECKING:
        subsidies: RelatedManager[Subsidy]

    class Meta:
        verbose_name_plural = "subsidy collectives"
        default_related_name = "collectives"
        ordering = ["coordinator__name"]

    @property
    def year_str(self):
        min_year = (
            self.subsidies.annotate(year=ExtractYear("date_from"))
            .values_list("year", flat=True)
            .order_by("year")
            .first()
        )
        max_year = (
            self.subsidies.annotate(year=ExtractYear("date_until"))
            .values_list("year", flat=True)
            .order_by("year")
            .last()
        )
        if min_year and max_year:
            if min_year == max_year:
                return str(min_year)
            return f"{min_year}-{max_year}"

    def __str__(self):
        if self.name:
            return self.name

        str_rep = f"Collective by {self.coordinator}"
        if self.year_str:
            str_rep += f" for {self.year_str}"

        return str_rep

    def get_absolute_url(self):
        return reverse("finances:subsidy_collective_details", args=(self.id,))
