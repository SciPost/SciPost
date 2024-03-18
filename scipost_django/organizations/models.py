__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
import hashlib
import pytz
import random
import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.urls import reverse

from django_countries.fields import CountryField

from .constants import (
    ORGANIZATION_TYPES,
    ORGTYPE_PRIVATE_BENEFACTOR,
    ORGANIZATION_STATUSES,
    ORGSTATUS_ACTIVE,
    ORGANIZATION_EVENTS,
    ROLE_KINDS,
)
from .managers import OrganizationQuerySet

from scipost.constants import TITLE_CHOICES
from scipost.fields import ChoiceArrayField
from scipost.models import Contributor
from affiliates.models import AffiliatePublication
from colleges.models import Fellowship
from finances.models import PubFrac
from journals.models import Journal, Publication
from profiles.models import Profile


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
    crossref_json = models.JSONField(
        default=dict, blank=True, null=True
    )  # JSON data from Crossref
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

    class Meta:
        ordering = ["country", "name"]
        permissions = (
            ("can_view_org_contacts", "Can view this Organization's Contacts"),
        )

    def __str__(self):
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
            publications = Publication.objects.published()
        if year:
            publications = publications.filter(publication_date__year=year)
        return publications.filter(pk__in=self.cf_associated_publication_ids["all"])

    def get_affiliate_publications(self, journal):
        return AffiliatePublication.objects.filter(
            pubfracs__organization=self,
            journal=journal,
        )

    def get_author_profiles(self):
        """
        Returns all Profiles of authors associated to this Organization.
        """
        profile_id_list = [
            tbl.profile.id
            for tbl in self.publicationauthorstable_set.all().select_related("profile")
        ]
        return (
            Profile.objects.filter(id__in=profile_id_list)
            .distinct()
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
        """
        ids = {
            "via_author_affiliation": [
                pk
                for pk in Publication.objects.published()
                .filter(authors__affiliations=self)
                .values_list("pk", flat=True)
            ],
            "via_grant": [
                pk
                for pk in Publication.objects.published()
                .filter(grants__funder__organization=self)
                .values_list("pk", flat=True)
            ],
            "via_funder_generic": [
                pk
                for pk in Publication.objects.published()
                .filter(funders_generic__organization=self)
                .values_list("pk", flat=True)
            ],
        }
        children_ids = [pk for pk in self.children.all().values_list("id", flat=True)]
        ids["via_child_author_affiliation"] = [
            pk
            for pk in Publication.objects.published()
            .filter(authors__affiliations__pk__in=children_ids)
            .values_list("pk", flat=True)
        ]
        ids["via_child_grant"] = [
            pk
            for pk in Publication.objects.published()
            .filter(grants__funder__organization__pk__in=children_ids)
            .values_list("pk", flat=True)
        ]
        ids["via_child_funder_generic"] = [
            pk
            for pk in Publication.objects.published()
            .filter(funders_generic__organization__pk__in=children_ids)
            .values_list("pk", flat=True)
        ]
        ids["all"] = list(
            set(
                ids["via_author_affiliation"]
                + ids["via_grant"]
                + ids["via_funder_generic"]
                + ids["via_child_author_affiliation"]
                + ids["via_child_grant"]
                + ids["via_child_funder_generic"]
            )
        )
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

    @property
    def has_current_subsidy(self):
        """
        Check if this organization has a Subsidy with a still-running validity period.
        """
        return (
            self.subsidy_set.obtained()
            .filter(date_until__gte=datetime.date.today())
            .exists()
        )

    @property
    def has_children_with_current_subsidy(self):
        for child in self.children.all():
            if child.has_current_subsidy:
                return True
        return False

    @property
    def latest_subsidy_date_until(self):
        """
        Returns the end date of validity of the latest subsidy.
        """
        if self.subsidy_set.obtained():
            return (
                self.subsidy_set.obtained().order_by("-date_until").first().date_until
            )
        return "-"

    def total_subsidies_in_year(self, year):
        """
        Return the total subsidies for this Organization in that year.
        """
        total = 0
        for subsidy in (
            self.subsidy_set.obtained()
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
            self.subsidy_set.obtained()
            .aggregate(models.Sum("amount"))
            .get("amount__sum", 0)
        )

    def get_total_subsidies_publicly_shown(self):
        """
        Computes the total amount of publicly visible Subsidies.
        """
        return (
            self.subsidy_set.obtained()
            .filter(amount_publicly_shown=True)
            .aggregate(models.Sum("amount"))
            .get("amount__sum", 0)
        )

    def get_balance_info(self):
        """
        Return a dict containing this Organization's expenditure and support history.
        """
        pubyears = range(int(timezone.now().strftime("%Y")), 2015, -1)
        rep = {}
        cumulative_nap = 0
        cumulative_pubfracs = 0
        cumulative_expenditures = 0
        cumulative_self_compensated = 0
        cumulative_ally_compensated = 0
        cumulative_uncompensated = 0
        cumulative_undivided_expenditures = 0
        cumulative_undivided_compensated = 0
        cumulative_undivided_uncompensated = 0
        cumulative_subsidy_income = 0
        cumulative_reserved = 0
        cumulative_balance = 0
        pf = self.pubfracs.all()
        publications_all = self.get_publications()
        for year in pubyears:
            rep[str(year)] = {}
            subsidy_income = self.total_subsidies_in_year(year)
            rep[str(year)]["subsidy_income"] = subsidy_income
            year_nap = 0
            year_undivided_expenditures = 0
            year_pubfracs = 0
            year_expenditures = 0
            year_self_compensated = 0
            year_ally_compensated = 0
            year_uncompensated = 0
            year_undivided_compensated = 0
            year_undivided_uncompensated = 0
            year_reserved = 0
            rep[str(year)]["expenditures"] = {
                "per_journal": {},
            }
            pfy = pf.filter(publication__publication_date__year=year)
            publications_year = publications_all.filter(publication_date__year=year)
            jl1 = [
                j
                for j in publications_year.values_list(
                    "in_journal__doi_label",
                    flat=True,
                )
                if j
            ]
            jl2 = [
                j
                for j in publications_year.values_list(
                    "in_issue__in_journal__doi_label",
                    flat=True,
                )
                if j
            ]
            jl3 = [
                j
                for j in publications_year.values_list(
                    "in_issue__in_volume__in_journal__doi_label",
                    flat=True,
                )
                if j
            ]
            journal_labels = set(jl1 + jl2 + jl3)
            for journal_label in journal_labels:
                qs = pfy.filter(publication__doi_label__istartswith=journal_label + ".")
                journal = get_object_or_404(Journal, doi_label=journal_label)
                publications_year_journal = self.get_publications(
                    year=year, journal=journal
                )
                nap = publications_year_journal.count()
                sum_pf = qs.aggregate(Sum("fraction"))["fraction__sum"] or 0
                costperpaper = journal.cost_per_publication(year)
                expenditures = int(costperpaper * sum_pf)
                self_compensated = int(
                    qs.filter(compensated_by__organization=self).aggregate(
                        Sum("cf_value")
                    )["cf_value__sum"]
                    or 0
                )
                ally_compensated = int(
                    qs.filter(compensated_by__isnull=False)
                    .exclude(compensated_by__organization=self)
                    .aggregate(Sum("cf_value"))["cf_value__sum"]
                    or 0
                )
                uncompensated = expenditures - self_compensated - ally_compensated
                undivided_compensated = int(
                    sum(
                        p.compensated_expenditures
                        for p in self.get_publications(year=year, journal=journal)
                    )
                )
                undivided_uncompensated = nap * costperpaper - undivided_compensated
                if sum_pf > 0 or undivided_uncompensated > 0:
                    rep[str(year)]["expenditures"]["per_journal"][journal_label] = {
                        "costperpaper": costperpaper,
                        "nap": nap,
                        "pubfracs": float(sum_pf),
                        "expenditures": expenditures,
                        "self_compensated": self_compensated,
                        "ally_compensated": ally_compensated,
                        "uncompensated": uncompensated,
                        "undivided_expenditures": nap * costperpaper,
                        "undivided_compensated": undivided_compensated,
                        "undivided_uncompensated": undivided_uncompensated,
                    }
                year_nap += nap
                year_undivided_expenditures += nap * costperpaper
                year_pubfracs += float(sum_pf)
                year_expenditures += expenditures
                year_self_compensated += self_compensated
                year_ally_compensated += ally_compensated
                year_uncompensated += uncompensated
                year_undivided_compensated += undivided_compensated
                year_undivided_uncompensated += undivided_uncompensated
            rep[str(year)]["expenditures"]["total"] = {
                "nap": year_nap,
                "pubfracs": year_pubfracs,
                "expenditures": year_expenditures,
                "self_compensated": year_self_compensated,
                "ally_compensated": year_ally_compensated,
                "uncompensated": year_uncompensated,
                "undivided_expenditures": year_undivided_expenditures,
                "undivided_compensated": year_undivided_compensated,
                "undivided_uncompensated": year_undivided_uncompensated,
            }
            rep[str(year)]["reserved"] = subsidy_income - year_self_compensated
            rep[str(year)]["balance"] = subsidy_income - year_expenditures
            cumulative_nap += year_nap
            cumulative_undivided_expenditures += year_undivided_expenditures
            cumulative_pubfracs += year_pubfracs
            cumulative_expenditures += year_expenditures
            cumulative_self_compensated += year_self_compensated
            cumulative_ally_compensated += year_ally_compensated
            cumulative_uncompensated += year_uncompensated
            cumulative_undivided_compensated += year_undivided_compensated
            cumulative_undivided_uncompensated += year_undivided_uncompensated
            cumulative_subsidy_income += subsidy_income
            cumulative_balance += subsidy_income - year_expenditures
            cumulative_reserved += subsidy_income - year_self_compensated
        rep["cumulative"] = {
            "nap": cumulative_nap,
            "undivided_expenditures": cumulative_undivided_expenditures,
            "pubfracs": cumulative_pubfracs,
            "expenditures": cumulative_expenditures,
            "self_compensated": cumulative_self_compensated,
            "ally_compensated": cumulative_ally_compensated,
            "uncompensated": cumulative_uncompensated,
            "undivided_compensated": cumulative_undivided_compensated,
            "undivided_uncompensated": cumulative_undivided_uncompensated,
            "subsidy_income": cumulative_subsidy_income,
            "reserved": cumulative_reserved,
            "balance": cumulative_balance,
        }
        return rep


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

    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=4, choices=TITLE_CHOICES)
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField()
    role = models.CharField(max_length=128)

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
