__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from decimal import Decimal
import hashlib
from itertools import chain, groupby
import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q, Count, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce, Lower
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse

from django.utils.functional import cached_property
from django_countries.fields import CountryField

from common.utils.attachments import (
    AttachableQuerySet,
    RelatedAttachment,
    attach_related,
)
from common.utils.lookups import ImmutableUnaccent
from finances.models.subsidy import Subsidy
from scipost.constants import TITLE_CHOICES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor
from affiliates.models import AffiliatePublication
from colleges.models import Fellowship
from finances.models import PubFrac
from journals.models import Journal, Publication
from profiles.models import Profile

from .constants import (
    ORGANIZATION_TYPES,
    ORGTYPE_PRIVATE_BENEFACTOR,
    ORGANIZATION_STATUSES,
    ORGSTATUS_ACTIVE,
    ORGANIZATION_EVENTS,
    ROLE_KINDS,
)
from .managers import OrganizationQuerySet

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class OrganizationLogo(models.Model):
    """
    Logo of an Organization, with rendering info, for a `source` HTML tag.
    """

    MIMETYPE_GIF = "gif"
    MIMETYPE_JPG = "jpg"
    MIMETYPE_PNG = "png"
    MIMETYPE_TIF = "tif"
    MITETYPE_WEBP = "webp"
    MIMETYPE_CHOICES = (
        (MIMETYPE_GIF, "gif"),
        (MIMETYPE_JPG, "jpg"),
        (MIMETYPE_PNG, "png"),
        (MIMETYPE_TIF, "tif"),
        (MITETYPE_WEBP, "webp"),
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        related_name="logos",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="organizations/logos/", blank=True)
    mimetype = models.CharField(max_length=8, choices=MIMETYPE_CHOICES)
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    order = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "order"],
                name="unique_together_organization_order",
            ),
        ]
        ordering = (
            "organization",
            "order",
        )

    def __str__(self):
        return (
            f"Logo ({self.mimetype}, w={self.width}, h={self.height}) "
            f"for {self.organization.name}"
        )

    def save(self, *args, **kwargs):
        if not self.order:
            self.order = self.organization.logos.count() + 1
        return super().save(*args, **kwargs)


class Organization(models.Model):
    """
    An Organization instance is any type of administrative unit which SciPost
    can interact with. Example types include universities, funding agencies,
    research institutes etc.

    All instances can only be created by SciPost administration-level personnel,
    and can thus be considered as verified.

    These objects are meant to be internally linked to all other types of
    (possibly user-defined) objects used throughout the site (such as Institutions,
    Partners, Affiliations, Funders etc). This enables relating all of SciPost's
    services to the organizations which are impacted by its activities.

    The data here is also meant to be cross-linked to external databases,
    for example the Global Research Identifier Database (GRID), Crossref,
    ORCID etc.
    """

    orgtype = models.CharField(max_length=32, choices=ORGANIZATION_TYPES)
    status = models.CharField(
        max_length=32, choices=ORGANIZATION_STATUSES, default=ORGSTATUS_ACTIVE
    )
    name = models.CharField(max_length=256, help_text="Western version of name")
    name_original = models.CharField(
        max_length=256, blank=True, help_text="Name (in original language)"
    )
    name_normalized = models.GeneratedField(
        expression=Lower(ImmutableUnaccent("name")),
        output_field=models.CharField(max_length=256),
        db_persist=True,
    )
    acronym = models.CharField(
        max_length=64, blank=True, help_text="Acronym or short name"
    )
    country = CountryField()
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to="organizations/logos/", blank=True)
    css_class = models.CharField(
        max_length=256, blank=True, verbose_name="Additional logo CSS class"
    )
    ror_json = models.JSONField(
        default=dict, blank=True, null=True
    )  # JSON data from ROR
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    superseded_by = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL
    )
    # Calculated fields (to save CPU; field name always starts with cf_)
    cf_associated_publication_ids = models.JSONField(
        blank=True,
        default=dict,
        help_text="NB: calculated field. Do not modify.",
    )
    cf_nr_associated_publications = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="NB: calculated field. Do not modify.",
    )
    cf_balance_info = models.JSONField(
        blank=True,
        default=dict,
        help_text="NB: calculated field. Do not modify.",
    )
    cf_expenditure_for_publication = models.JSONField(
        blank=True,
        default=dict,
        help_text="NB: calculated field. Do not modify.",
    )

    objects = OrganizationQuerySet.as_manager()

    if TYPE_CHECKING:
        subsidies: RelatedManager[Subsidy]
        pubfracs: RelatedManager[PubFrac]

    class Meta:
        ordering = ["country", "name"]
        permissions = (
            ("can_view_org_contacts", "Can view this Organization's Contacts"),
        )

    def __str__(self):
        return self.name

    @property
    def name_prose(self):
        """
        Return the name in a prose-like format.
        E.g. "the University of Amsterdam" instead of "University of Amsterdam".
        """
        if " of " in self.name or " for " in self.name:
            return "the " + self.name
        return self.name

    @property
    def full_name(self):
        full_name_str = ""
        if self.name_original:
            full_name_str += "%s / " % self.name_original
        full_name_str += "%s" % self.name
        return full_name_str

    @property
    def full_name_with_acronym(self):
        full_name_str = self.full_name
        if self.acronym:
            full_name_str += " [%s]" % self.acronym
        return full_name_str

    def get_absolute_url(self):
        return reverse("organizations:organization_detail", kwargs={"pk": self.id})

    @property
    def details_publicly_viewable(self):
        return self.orgtype != ORGTYPE_PRIVATE_BENEFACTOR

    def get_publications(self, year=None, journal=None):
        if "all" not in self.cf_associated_publication_ids:
            return Publication.objects.none()
        if journal and isinstance(journal, Journal):
            publications = journal.get_publications()
        else:
            # Since `journal.get_publications()` returns all pubs and not just non-draft ones,
            # perhaps we should also return all pubs here too.
            publications = Publication.objects.ever_published()
        if year:
            publications = publications.filter(publication_date__year=year)
        return publications.filter(pk__in=self.cf_associated_publication_ids["all"])

    def get_publications_with_year(self, year=None, journal=None):
        publications = self.get_publications(year=year, journal=journal).annotate(
            publication_year=F("publication_date__year"),
            org_attributed_pubfrac_id=Subquery(
                PubFrac.objects.filter(
                    publication=OuterRef("pk"),
                    organization=self,
                ).values("id")[:1]
            ),
        )

        return AttachableQuerySet.from_queryset(publications).attach(
            RelatedAttachment(
                "org_attributed_pubfrac_id",
                "org_attributed_pubfrac",
                PubFrac.objects.select_related("compensated_by__organization"),
            )
        )

    def get_affiliate_publications(self, journal):
        return AffiliatePublication.objects.filter(
            pubfracs__organization=self,
            journal=journal,
        )

    def get_ally_compensated_pubfracs(self):
        return (
            PubFrac.objects.filter(
                organization=self, publication__in=self.get_publications()
            )
            .exclude(compensated_by__isnull=True)
            .exclude(compensated_by__organization=self)
        )

    def get_ally_compensation_stats(self):
        """
        Returns a dict with statistics about the ally compensation for this Organization.
        """

        return (
            self.get_ally_compensated_pubfracs()
            .values("compensated_by__organization")
            .annotate(
                amount=Sum("cf_value"),
                count=Count("publication", distinct=True),
                id=F("compensated_by__organization__id"),
                name=F("compensated_by__organization__name"),
            )
            .order_by("-amount")
            .values("id", "name", "amount", "count")
        )

    def get_author_profiles(self):
        """
        Returns all Profiles of authors associated to this Organization.
        """
        author_profile_ids = self.publicationauthorstable_set.values("profile_id")
        return (
            Profile.objects.all()
            .filter(id__in=author_profile_ids)
            .select_related("contributor")
        )

    def fellowships(self, year=None):
        """
        Fellowships with Fellow having listed this organization as affiliation.

        If `year` is given, filter for affiliation and fellowship both valid in that year.
        """
        affiliations = self.affiliations.all()
        if year is not None:
            affiliations = affiliations.filter(
                Q(date_from__isnull=True) | Q(date_from__year__lte=year),
                Q(date_until__isnull=True) | Q(date_until__year__gte=year),
            )
        profile_ids = [a.profile.id for a in affiliations.select_related("profile")]
        fellowships = Fellowship.objects.filter(
            contributor__profile__id__in=profile_ids
        )
        if year is not None:
            fellowships = fellowships.active_in_year(year)
        return fellowships

    def count_publications(self):
        return self.get_publications().count()

    def update_cf_associated_publication_ids(self):
        """
        Update the calculated field Organization:cf_associated_publication_ids.
        !Warning: "via_*" keys are not using "distinct" and could contain duplicates.
        """
        published_pks = Publication.objects.ever_published().values_list("pk", flat=True)
        children_ids = list(self.children.all().values_list("id", flat=True))
        ids: dict[str, list[int]] = {
            "via_author_affiliation": list(
                published_pks.filter(authors__affiliations=self)
            ),
            "via_grant": list(published_pks.filter(grants__funder__organization=self)),
            "via_funder_generic": list(
                published_pks.filter(funders_generic__organization=self)
            ),
            "via_child_author_affiliation": list(
                published_pks.filter(authors__affiliations__pk__in=children_ids)
            ),
            "via_child_grant": list(
                published_pks.filter(grants__funder__organization__pk__in=children_ids)
            ),
            "via_child_funder_generic": list(
                published_pks.filter(funders_generic__organization__pk__in=children_ids)
            ),
        }
        ids["all"] = list(set(chain.from_iterable(ids.values())))
        self.cf_associated_publication_ids = ids
        self.save()

    def update_cf_nr_associated_publications(self):
        """
        Update the calculated field Organization:cf_nr_associated_publications.
        """
        self.cf_nr_associated_publications = self.count_publications()
        self.save()

    def update_cf_balance_info(self):
        """
        Update the calculated field Organization:cf_balance_info.
        """
        self.cf_balance_info = self.get_balance_info()
        self.save()

    def pubfrac_for_publication(self, doi_label):
        """
        Return the organization's pubfrac for a publication.
        """
        pfs = PubFrac.objects.filter(publication__doi_label=doi_label)
        try:
            return pfs.get(organization=self).fraction
        except PubFrac.DoesNotExist:
            children_ids = [k["id"] for k in list(self.children.all().values("id"))]
            children_contribs = pfs.filter(organization__id__in=children_ids).aggregate(
                Sum("fraction")
            )["fraction__sum"]
            if children_contribs is not None:
                message = "as parent (ascribed to "
                for child in self.children.all():
                    pfc = child.pubfrac_for_publication(doi_label)
                    if pfc not in ["No PubFrac ascribed", "Not yet defined"]:
                        message += "%s: %s; " % (child, pfc)
                return message.rpartition(";")[0] + ")"
        return "Not yet defined"

    def expenditure_for_publication(self, doi_label):
        """
        Return publication's expenditure details related to this organization.
        """
        publication = get_object_or_404(Publication, doi_label=doi_label)
        unitcost = publication.get_journal().cost_per_publication(
            publication.publication_date.year
        )
        try:
            pf = PubFrac.objects.get(
                publication=publication,
                organization=self,
            )
            return {
                "millipubfrac": int(1000 * pf.fraction),
                "unitcost": unitcost,
                "expenditure": int(pf.fraction * unitcost),
                "message": "",
            }
        except PubFrac.DoesNotExist:
            pass
        children_ids = [k["id"] for k in list(self.children.all().values("id"))]
        children_contrib_ids = set(
            c
            for c in PubFrac.objects.filter(
                publication=publication,
                organization__id__in=children_ids,
            ).values_list("organization__id", flat=True)
        )
        message = ""
        if children_contrib_ids:
            message = "as parent (ascribed to "
            for child in self.children.filter(pk__in=children_contrib_ids):
                message += f"{child}; "
            message = message.rpartition(";")[0] + ")"
        return {
            "millipubfrac": 0,
            "unitcost": unitcost,
            "expenditure": 0,
            "message": message,
        }

    def pubfracs_in_year(self, year):
        """
        Returns the sum of pubfracs for the given year.
        """
        fractions = PubFrac.objects.filter(
            organization=self, publication__publication_date__year=year
        )
        return {
            "total": fractions.aggregate(Sum("fraction"))["fraction__sum"],
        }

    def has_pubfracs(self):
        """Whether this Organization is mentioned in any author affiliation."""
        return self.pubfracs.exists()

    @cached_property
    def has_current_subsidy(self):
        """
        Check if this organization has a Subsidy with a still-running validity period.
        """
        return (
            self.subsidies.obtained()
            .filter(date_until__gte=datetime.date.today())
            .exists()
        )

    @cached_property
    def has_children_with_current_subsidy(self):
        for child in self.children.all():
            if child.has_current_subsidy:
                return True
        return False

    @cached_property
    def has_any_subsidy(self):
        """
        Check if this organization has any Subsidy.
        """
        return self.subsidies.obtained().exists()

    @property
    def latest_subsidy_date_until(self):
        """
        Returns the end date of validity of the latest subsidy.
        """
        if self.subsidies.obtained():
            return self.subsidies.obtained().order_by("-date_until").first().date_until
        return "-"

    def total_subsidies_in_year(self, year):
        """
        Return the total subsidies for this Organization in that year.
        """
        total = 0
        for subsidy in (
            self.subsidies.obtained()
            .filter(date_from__year__lte=year)
            .filter(models.Q(date_until=None) | models.Q(date_until__year__gte=year))
        ):
            total += subsidy.value_in_year(year)
        return total

    def get_total_subsidies_obtained(self):
        """
        Computes the total amount received by SciPost, in the form
        of subsidies from this Organization.
        """
        return (
            self.subsidies.obtained()
            .aggregate(models.Sum("amount"))
            .get("amount__sum", 0)
        )

    def get_total_subsidies_publicly_shown(self):
        """
        Computes the total amount of publicly visible Subsidies.
        """
        return (
            self.subsidies.obtained()
            .filter(amount_publicly_shown=True)
            .aggregate(models.Sum("amount"))
            .get("amount__sum", 0)
        )

    def get_balance_info(self):
        """
        Return a dict containing this Organization's expenditure and support history.
        The dict is structured as follows:
        ```{
            "cumulative": {
                "nap": 0,
                "pubfracs": 0.0,
                "expenditures": 0.0,
                "associated_expenditures": 0.0,
                "associated_compensated": 0.0,
                "associated_uncompensated": 0.0,
                "associated_uncompensated_inflated": 0.0,
                "self_compensated": 0.0,
                "ally_compensated": 0.0,
                "uncompensated": 0.0,
                "uncompensated_inflated": 0.0,
                "bystander_percentage": 0.0,
                "subsidy_income": 0.0,
                "reserved": 0.0,
                "impact_on_reserves": 0.0
            },
            "YYYY": {
                "subsidy_income": 0.0,
                "reserved": 0.0,
                "impact_on_reserves": 0.0,
                "expenditures": {
                    "total":  {
                        "nap": 0,
                        "pubfracs": 0.0,
                        "expenditures": 0.0,
                        "associated_expenditures": 0.0,
                        "associated_compensated": 0.0,
                        "associated_uncompensated": 0.0,
                        "associated_uncompensated_inflated": 0.0,
                        "self_compensated": 0.0,
                        "ally_compensated": 0.0,
                        "uncompensated": 0.0,
                        "uncompensated_inflated": 0.0,
                        "bystander_percentage": 0.0
                    },
                    "per_journal": {
                        "JOURNAL_DOI_LABEL": {
                            "nap": 0,
                            "pubfracs": 0.0,
                            "expenditures": 0.0,
                            "associated_expenditures": 0.0,
                            "associated_compensated": 0.0,
                            "associated_uncompensated": 0.0,
                            "associated_uncompensated_inflated": 0.0,
                            "self_compensated": 0.0,
                            "ally_compensated": 0.0,
                            "uncompensated": 0.0,
                            "uncompensated_inflated": 0.0,
                            "bystander_percentage": 0.0
                        }
                    }
                }
            }
        }```
        """
        current_year = timezone.now().year
        publication_years = range(current_year, 2015, -1)

        # Source: https://opendata.cbs.nl/#/CBS/nl/dataset/71905ned/table
        inflation = 1  # Start at 1, multiply in the year loop.
        INFLATION_RATES = {
            2016: 1.013,
            2017: 1.013,
            2018: 1.013,
            2019: 1.013,
            2020: 1.013,
            2021: 1.027,
            2022: 1.100,
            2023: 1.037,
            2024: 1.033,
            2025: 1.033,
            current_year: 1.000,
        }

        DEFAULT_EXPENDITURES = {
            "nap": 0.0,
            "pubfracs": 0.0,
            "expenditures": 0.0,
            "associated_expenditures": 0.0,
            "associated_compensated": 0.0,
            "associated_uncompensated": 0.0,
            "associated_uncompensated_inflated": 0.0,
            "self_compensated": 0.0,
            "ally_compensated": 0.0,
            "uncompensated": 0.0,
            "uncompensated_inflated": 0.0,
            "bystander_percentage": 0.0,
        }
        DEFAULT_NON_EXPENDITURES = {
            "subsidy_income": 0.0,
            "reserved": 0.0,
            "impact_on_reserves": 0.0,
        }

        compensated_pubfrac_total_amount = (
            PubFrac.objects.filter(
                publication=OuterRef("pk"),
                compensated_by__isnull=False,
            )
            .values("publication")
            .annotate(total=Sum("cf_value"))
            .values("total")[:1]
        )
        publications = (
            self.get_publications()
            .annotate(
                amount_compensated=Coalesce(
                    Subquery(compensated_pubfrac_total_amount), Decimal(0)
                ),
                journal_id=Coalesce(
                    "in_issue__in_volume__in_journal__id",
                    "in_issue__in_journal__id",
                    "in_journal__id",
                ),
                pubfrac_id=Subquery(
                    PubFrac.objects.all()
                    .filter(
                        publication=OuterRef("pk"),
                        organization=self,
                    )
                    .values("id")[:1]
                ),
            )
            .order_by("-publication_date__year", "journal_id")
        )

        Q_self_compensated = Q(compensated_by__organization=F("organization"))
        attach_related(
            publications,
            RelatedAttachment[Journal, Publication](
                "journal_id",
                "journal",
                Journal.objects.all(),
            ),
            RelatedAttachment[PubFrac, Publication](
                "pubfrac_id",
                "pubfrac",
                PubFrac.objects.all().annotate(
                    is_compensated=Q(compensated_by__isnull=False),
                    is_self_compensated=Q(is_compensated=True) & Q_self_compensated,
                    is_ally_compensated=Q(is_compensated=True) & ~Q_self_compensated,
                ),
            ),
        )

        balance_info = {}
        cumulative_stats = balance_info.setdefault(
            "cumulative",
            {
                **DEFAULT_EXPENDITURES.copy(),
                **DEFAULT_NON_EXPENDITURES.copy(),
            },
        )

        for year in publication_years:
            inflation *= INFLATION_RATES.get(year, 1.013 if year <= 2020 else 1.033)

            year_group = [p for p in publications if p.publication_date.year == year]
            year_info = balance_info.setdefault(
                str(year), DEFAULT_NON_EXPENDITURES.copy()
            )
            year_expenditures = year_info.setdefault("expenditures", {})
            per_journal_expenditures = year_expenditures.setdefault("per_journal", {})
            year_expenditure_totals = year_expenditures.setdefault(
                "total", DEFAULT_EXPENDITURES.copy()
            )

            for journal, journal_group in groupby(year_group, key=lambda p: p.journal):
                journal_group = list(journal_group)
                journal_expenditures = per_journal_expenditures.setdefault(
                    journal.doi_label, {}
                )

                cost_per_paper = journal.cost_per_publication(year)
                nap = len(journal_group)
                associated_expenditures = cost_per_paper * nap
                associated_compensated = sum(
                    pub.amount_compensated for pub in journal_group
                )
                associated_uncompensated = (
                    associated_expenditures - associated_compensated
                )

                pubfracs = Decimal(0)
                expenditures = Decimal(0)
                uncompensated = Decimal(0)
                self_compensated = Decimal(0)
                ally_compensated = Decimal(0)
                for pub in journal_group:
                    if not (pubfrac := pub.pubfrac):
                        continue
                    fraction, value = pubfrac.fraction, pubfrac.cf_value

                    pubfracs += fraction
                    expenditures += value
                    if not pubfrac.is_compensated:
                        uncompensated += value
                    elif pubfrac.is_self_compensated:
                        self_compensated += value
                    elif pubfrac.is_ally_compensated:
                        ally_compensated += value

                # Add to journal stats
                journal_stats = {
                    "nap": nap,
                    "pubfracs": float(pubfracs),
                    "expenditures": float(expenditures),
                    "associated_expenditures": float(associated_expenditures),
                    "associated_compensated": float(associated_compensated),
                    "associated_uncompensated": float(associated_uncompensated),
                    "associated_uncompensated_inflated": float(associated_uncompensated)
                    * inflation,
                    "self_compensated": float(self_compensated),
                    "ally_compensated": float(ally_compensated),
                    "uncompensated": float(uncompensated),
                    "uncompensated_inflated": float(uncompensated) * inflation,
                }
                journal_expenditures.update(
                    {
                        **journal_stats,
                        "costperpaper": float(cost_per_paper),
                        "bystander_percentage": float(
                            100 * uncompensated / expenditures
                        )
                        if expenditures > 0
                        else 0.0,
                    }
                )

                # Add to journal expenditures to yearly and cumulative expenditures
                for key, journal_stat in journal_stats.items():
                    year_expenditure_totals[key] += journal_stat
                    cumulative_stats[key] += journal_stat

            # Update yearly expenditure info
            year_expenditures = year_expenditure_totals.get("expenditures", 0.0)
            year_uncompensated = year_expenditure_totals.get("uncompensated", 0.0)
            year_expenditure_totals.update(
                {
                    "bystander_percentage": (
                        float(100 * year_uncompensated / year_expenditures)
                        if year_expenditures > 0
                        else 0.0
                    ),
                }
            )

            # Update yearly subsidy info
            subsidy_income = self.total_subsidies_in_year(year)
            year_self_compensated = year_expenditure_totals.get("self_compensated", 0.0)
            year_info.update(
                {
                    "subsidy_income": float(subsidy_income),
                    "reserved": float(subsidy_income - year_self_compensated),
                    "impact_on_reserves": float(subsidy_income - year_expenditures),
                }
            )

            # Add yearly subsidy info to cumulative subsidy info
            for key, year_stat in year_info.items():
                if key == "expenditures":
                    continue
                cumulative_stats[key] += year_stat

        cumulative_uncompensated = cumulative_stats.get("uncompensated", 0.0)
        cumulative_expenditures = cumulative_stats.get("expenditures", 0.0)
        cumulative_stats.update(
            {
                "bystander_percentage": (
                    float(100 * cumulative_uncompensated / cumulative_expenditures)
                    if cumulative_expenditures > 0
                    else 0.0
                )
            }
        )

        return balance_info

    def get_sponsorship_email_content(self):
        """
        Renders the content of a renewal email for this Organization, based on its subsidy status and history.
        """
        from math import ceil, log10

        from django.template.loader import get_template

        tiers: list[dict[str, Any]] = [
            {"name": tier, "amount": 0}
            for attr in dir(self)
            if attr.startswith("tier_") and (tier := attr.removeprefix("tier_"))
        ]

        for tier in tiers[::-1]:
            amount = getattr(self, "tier_" + tier["name"], 0)

            # Round to a magnitude-appropriate quarter-multiple (25 * 10**n)
            if amount > 0:
                digits = max(0, ceil(log10(amount)) - 3)
                step = 25 * 10**digits
                rounded_amount = round(amount / step) * step
            else:
                rounded_amount = 0

            tier["amount"] = amount
            tier["rounded_amount"] = rounded_amount

        # Only keep tiers with a rounded amount greater than 1k,
        # other amounts do not outweigh the administrative cost
        tiers = list(filter(lambda x: x.get("rounded_amount", 0) >= 1000, tiers))
        tiers.sort(key=lambda x: x.get("rounded_amount", 0))

        sponsorship_years = sorted({s["year"] for s in self.sponsorships})
        latest_subsidy_year = sponsorship_years[-1] if sponsorship_years else 0
        year = timezone.now().year

        try:
            context = {
                "org": self,
                "org_name_prose": self.name_prose,
                "sponsored_in_past": self.has_any_subsidy,
                "years_of_sponsorship": len(sponsorship_years),
                "latest_subsidy_nearing_expiration": latest_subsidy_year == year,
                "latest_subsidy_expired": latest_subsidy_year < year,
                "number_of_papers": self.cf_nr_associated_publications,
                "number_of_authors": self.nr_authors,
                "number_of_profiles_affiliated": self.nr_affiliated,
                "number_of_fellows": self.nr_fellows,
                "number_of_papers_in_year_actual": round(self.nap_this_year_actual),
                "number_of_papers_in_year_projected": round(
                    self.nap_this_year_projected
                ),
                "number_of_papers_in_year_projection_delta": round(
                    self.nap_this_year_projection_delta
                ),
                "number_of_papers_uncompensated": round(
                    self.nr_uncompensated_publications
                ),
                "pubfracs_uncompensated": round(
                    self.sum_uncompensated_pubfracs_fraction, 2
                ),
                "pubfracs_uncompensated_value": round(
                    self.sum_uncompensated_pubfracs_value
                ),
                "uncompensated_expenditures_this_year_projected": round(
                    self.uncomp_expend_this_year_projected
                ),
                "sponsorship_tiers": tiers,
            }
        except AttributeError as e:
            raise ValueError(
                "Organization instance is missing required attributes for rendering the renewal email content: "
                + str(e)
            )

        template = get_template("organizations/organization_sponsorship_email.html")
        return template.render(context)


###################################
# Events related to Organizations #
###################################


class OrganizationEvent(models.Model):
    """
    Documents an event related to an Organization.
    """

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    event = models.CharField(max_length=64, choices=ORGANIZATION_EVENTS)
    comments = models.TextField(blank=True)
    noted_on = models.DateTimeField(default=timezone.now)
    noted_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-noted_on", "organization"]

    def __str__(self):
        return "%s: %s" % (str(self.organization), self.get_event_display())


####################################
# Contact persons, users and roles #
####################################


class ContactPerson(models.Model):
    """
    A ContactPerson instance holds information about a person who can function
    as a contact for one or more organizations.
    These instances are created by SPAdmin during sponsor harvesting.
    Instances can be promoted to Contact instances, which possess login credentials.
    """

    STATUS_UNKNOWN = "unknown"
    STATUS_ACTIVE = "active"
    STATUS_DEPRECATED = "deprecated"
    STATUS_CHOICES = (
        (STATUS_UNKNOWN, "Unknown"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_DEPRECATED, "Deprecated"),
    )

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()
    role = models.CharField(max_length=128, blank=True, null=True)
    info_source = models.TextField(blank=True, verbose_name="Information source")
    status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_UNKNOWN
    )
    date_deprecated = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["last_name", "first_name", "organization"]

    def __str__(self):
        return "%s %s %s" % (self.get_title_display(), self.first_name, self.last_name)


class Contact(models.Model):
    """
    A Contact instance is a basic User to be used for Organization-type contacts.
    Specific Organizations are linked to Contact via the ContactRole model defined below.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, unique=True, related_name="org_contact"
    )
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    activation_key = models.CharField(max_length=40, blank=True)
    key_expires = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return "%s %s, %s" % (
            self.get_title_display(),
            self.user.last_name,
            self.user.first_name,
        )

    def generate_key(self, feed=""):
        """
        Generate and save a new activation_key for the Contact, given a certain feed.
        """
        for i in range(5):
            feed += random.choice(string.ascii_letters)
        feed = feed.encode("utf8")
        salt = self.user.username.encode("utf8")
        self.activation_key = hashlib.sha1(salt + feed).hexdigest()
        self.key_expires = timezone.now() + datetime.timedelta(days=2)

    def save(self, *args, **kwargs):
        if not self.activation_key:
            self.generate_key()
        super().save(*args, **kwargs)


class ContactRole(models.Model):
    """
    A ContactRole instance links a Contact to an Organization, for a specific set of roles
    and for a specific period in time.
    """

    contact = models.ForeignKey(
        "organizations.Contact", on_delete=models.CASCADE, related_name="roles"
    )
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    kind = ChoiceArrayField(models.CharField(max_length=4, choices=ROLE_KINDS))
    date_from = models.DateField()
    date_until = models.DateField()

    def __str__(self):
        return "%s, %s for %s" % (
            self.contact,
            self.get_kind_display,
            self.organization,
        )

    @property
    def get_kind_display(self):
        """
        Due to a lack of support to use get_FOO_display in a ArrayField, one has to create
        one 'manually'.
        """
        choices = dict(ROLE_KINDS)
        return ", ".join([choices[value] for index, value in enumerate(self.kind)])
