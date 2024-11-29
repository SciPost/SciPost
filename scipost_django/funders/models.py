__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db import models
from django.db.models import Q
from django.forms import ValidationError
from django.urls import reverse

from journals.models import Publication
from organizations.models import Organization
from profiles.models import Profile
from scipost.models import Contributor

from .managers import FunderQuerySet

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager
    from finances.models.subsidy import Subsidy


class Funder(models.Model):
    """
    A Funder instance is an organization present in the Fundref registry.

    Funding info metadata, which is deposited with our normal metadata deposits
    to Crossref (via Grants or generic Funders), is linked back to funders
    through Crossref's Crossmark service.
    """

    name = models.CharField(max_length=256)
    acronym = models.CharField(max_length=32, blank=True)
    identifier = models.CharField(max_length=200, unique=True)
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE, blank=True, null=True
    )

    objects = FunderQuerySet.as_manager()

    class Meta:
        ordering = ["name", "acronym"]

    def __str__(self):
        result = self.name
        if self.acronym:
            result += " (%s)" % self.acronym
        return result

    def get_absolute_url(self):
        """Return the Funder detail page."""
        return reverse("funders:funder_publications", args=(self.id,))

    def all_related_publications(self):
        """Return all Publication objects linked to this Funder."""
        return Publication.objects.filter(
            Q(funders_generic=self) | Q(grants__funder=self)
        ).distinct()


class Grant(models.Model):
    """An instance of a grant, award or other funding.

    In a Publication's metadata, all grants are listed
    in the Crossmark part of the metadata.
    """

    funder = models.ForeignKey("funders.Funder", on_delete=models.CASCADE)
    number = models.CharField(max_length=64)
    recipient_name = models.CharField(max_length=64, blank=True)
    recipient = models.ForeignKey(
        "scipost.Contributor", blank=True, null=True, on_delete=models.CASCADE
    )
    further_details = models.CharField(max_length=256, blank=True)

    class Meta:
        default_related_name = "grants"
        ordering = ["funder", "recipient", "recipient_name", "number"]
        unique_together = ("funder", "number")

    def __str__(self):
        grantstring = "%s, grant number %s" % (str(self.funder), self.number)
        if self.recipient:
            grantstring += " (%s)" % str(self.recipient)
        elif self.recipient_name:
            grantstring += " (%s)" % self.recipient_name
        if self.further_details:
            grantstring += " [%s]" % self.further_details
        return grantstring


class IndividualBudget(models.Model):
    """
    Generic structure of a budget from an Organization given to a single individual.
    The funding source of individual subsidies.
    """

    required_css_class = "required-asterisk"

    description = models.TextField(blank=True)
    organization = models.ForeignKey["Organization"](
        "organizations.Organization", on_delete=models.CASCADE, blank=True, null=True
    )
    holder = models.ForeignKey["Profile"](
        "profiles.Profile", on_delete=models.CASCADE, blank=True, null=True
    )
    budget_number = models.CharField(max_length=64, blank=True, null=True)
    fundref_id = models.CharField(max_length=64, blank=True, null=True)

    if TYPE_CHECKING:
        subsidies_funded: "RelatedManager[Subsidy]"

    class Meta:
        default_related_name = "individual_budgets"
        ordering = ["organization", "holder"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "budget_number"],
                name="unique_organization_budget_number",
                violation_error_message="This organization already has a budget with this number.",
            ),
            models.CheckConstraint(
                check=~models.Q(organization=None, holder=None),
                name="organization_or_holder_must_be_set",
                violation_error_message="Either an organization or a holder must be set for the budget.",
            ),
        ]

    def get_absolute_url(self):
        return reverse(
            "funders:individual_budget_details", kwargs={"budget_id": self.id}
        )

    @property
    def name(self):
        if self.budget_number:
            return f"Budget {self.budget_number}"
        return "Unnamed budget"

    def __str__(self):
        str_repr = f"{self.name} from {self.organization}"
        if self.holder:
            str_repr += f" to {self.holder}"

        return str_repr
