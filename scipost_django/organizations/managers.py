__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import calendar
import datetime
from itertools import chain

from django.contrib.postgres.expressions import ArraySubquery
from django.contrib.postgres.lookups import Unaccent
from django.db import models
from django.db.models import (
    F,
    Q,
    Count,
    Exists,
    FloatField,
    IntegerField,
    OuterRef,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Cast, Coalesce, JSONObject, Round
from django.utils import timezone

from common.utils.models import qs_duplicates_group_by_key, queryset_annotation
from finances.constants import (
    SUBSIDY_PROMISED,
    SUBSIDY_INVOICED,
    SUBSIDY_RECEIVED,
    SUBSIDY_WITHDRAWN,
)
from finances.models.pubfrac import PubFrac
from finances.models.subsidy import Subsidy

from typing import Any, Mapping, TYPE_CHECKING, Type

if TYPE_CHECKING:
    from organizations.models import Organization


class OrganizationQuerySet(models.QuerySet):
    def all_sponsors(self):
        """
        All Organizations which have subsidized SciPost at least once in the past.
        """
        return self.filter(
            subsidies__status__in=[
                SUBSIDY_PROMISED,
                SUBSIDY_INVOICED,
                SUBSIDY_RECEIVED,
            ],
            subsidies__amount__gte=0,
        )

    def current_sponsors(self):
        """
        Organizations which have a Subsidy which is ongoing (date_until <= today).
        """
        return (
            self.all()
            .filter(subsidies__date_until__gte=datetime.date.today())
            .exclude(subsidies__status=SUBSIDY_WITHDRAWN)
        )

    def with_subsidy_above_and_up_to(self, min_amount, max_amount=None):
        """
        List of sponsors with at least one subsidy above parameter:amount.
        """
        qs = (
            self.filter(
                subsidies__status__in=[
                    SUBSIDY_PROMISED,
                    SUBSIDY_INVOICED,
                    SUBSIDY_RECEIVED,
                ],
            )
            .annotate(max_subsidy=models.Max("subsidies__amount"))
            .filter(max_subsidy__gte=min_amount)
        )
        if max_amount:
            qs = qs.filter(max_subsidy__lt=max_amount)
        return qs

    def order_by_total_amount_received(self):
        """
        Order by (decreasing) total amount received.
        """
        return (
            self.filter(
                subsidies__status__in=[
                    SUBSIDY_PROMISED,
                    SUBSIDY_INVOICED,
                    SUBSIDY_RECEIVED,
                ],
            )
            .annotate(total=models.Sum("subsidies__amount"))
            .order_by("-total")
        )

    def order_by_yearly_coverage(self, year_start=None, year_end=None):
        """
        Order by average yearly coverage between year_start and year_end.
        If either year_start or year_end is None, assume interminable coverage of that end.
        """
        subsidy_filter = Q(organization=models.OuterRef("pk"))

        # If year_start and year_end are both None, no filtering is needed.
        # If year_start is None, filter such that date_until <= year_end.
        # If year_end is None, filter such that year_start <= date_from.
        # If both are specified, filter such that
        # date_from <= year_start <= year_end <= date_until.
        match (year_start, year_end):
            case (None, None):
                pass
            case (None, _):
                subsidy_filter &= Q(date_until__year__lte=year_end)
            case (_, None):
                subsidy_filter &= Q(date_from__year__gte=year_start)
            case (_, _):
                subsidy_filter &= Q(date_from__year__lte=year_start)
                subsidy_filter &= Q(date_until__year__gte=year_end)

        return (
            self.annotate(
                total_yearly_coverage=models.Subquery(
                    Subsidy.objects.obtained()
                    .filter(subsidy_filter)
                    .annotate(
                        yearly_coverage=models.F("amount")
                        / (
                            1
                            + models.F("date_until__year")
                            - models.F("date_from__year")
                        )
                    )
                    .values("organization")
                    .annotate(total=models.Sum("yearly_coverage"))
                    .values("total")
                )
            )
            .order_by(models.F("total_yearly_coverage").desc(nulls_last=True))
            .distinct()
        )

    def get_potential_duplicates(self) -> "Mapping[Any, list[Organization]]":
        """
        Returns a mapping of potential duplicate Organization, keyed by the normalized name.
        """
        return {
            group: list(items)
            for group, items in chain(
                qs_duplicates_group_by_key(self, "name_normalized"),
                qs_duplicates_group_by_key(self, "ror_json__id"),
            )
        }

    def annot_has_current_subsidy(self):
        """
        Annotate with a boolean indicating whether the Organization has a current subsidy.
        """
        return self.annotate(
            has_current_subsidy=Exists(
                Subsidy.objects.obtained()
                .filter(date_until__gte=timezone.now())
                .filter(organization=OuterRef("pk"))
            )
        )

    def annot_has_children_with_current_subsidy(self):
        """
        Annotate with a boolean indicating whether the Organization has children with a current subsidy.
        """
        return self.annotate(
            has_children_with_current_subsidy=Exists(
                Subsidy.objects.filter(organization__in=models.OuterRef("children"))
                .obtained()
                .filter(date_until__gte=timezone.now())
            )
        )

    def annot_has_any_subsidy(self):
        return self.annotate(
            has_any_subsidy=Exists(
                Subsidy.objects.all().obtained().filter(organization=OuterRef("pk"))
            )
        )

    @queryset_annotation
    def annot_latest_subsidy_id(self):
        """
        Annotate with the latest Subsidy for the Organization.
        Latest is defined as a current subsidy extending furthest into the future,
        or if there are no current subsidies, the most recent past subsidy.
        """
        return Coalesce(
            Subquery(
                Subsidy.objects.current()
                .filter(organization=OuterRef("pk"))
                .order_by("-date_until")
                .values("id")[:1]
            ),
            Subquery(
                Subsidy.objects.obtained()
                .filter(organization=OuterRef("pk"))
                .order_by("-date_from")
                .values("id")[:1]
            ),
            output_field=models.IntegerField(),
        )

    @queryset_annotation
    def annot_latest_ally_subsidy_id_for_any_compensated_pubfrac(self):
        """
        Annotate with the latest Subsidy of any allied Organization which had compensated a PubFrac for this Organization.
        """

        # fmt: off
        return Subquery(
            Subsidy.objects.all()
            # The lookup `organization__subsidies__compensated_pubfracs(__organization)` means:
            # "Find other subsidies from an organization which has compensated some PubFrac attributed to me"
            .filter(organization__subsidies__compensated_pubfracs__organization=OuterRef("id"))
            .exclude(
                # Exclude compensation strategies that are too broad
                # to warrant allyship across all future subsidies
                organization__subsidies__compensated_pubfracs__compensated_by__compensation_strategies_keys__contained_by=[
                    # "countries",
                    # "funders",
                    # "specialties",
                    "any",
                ]
            )
            # Exclude subsidies from the same organization, as those would not be "ally" subsidies but "self" subsidies
            .exclude(organization__subsidies__organization=OuterRef("id"))
            .order_by("-date_from")
            .values("id")[:1]
        )
        # fmt: on

    @queryset_annotation
    def annot_nr_authors(self):
        """
        Annotate with the number of authors affiliated with this Organization.
        """
        from journals.models import PublicationAuthorsTable

        author_counts = (
            PublicationAuthorsTable.objects.filter(affiliations__pk=OuterRef("pk"))
            .order_by()
            .values("affiliations__pk")
            .annotate(total=Count("profile_id", distinct=True))
            .values("total")[:1]
        )
        return Coalesce(Subquery(author_counts), Value(0))

    @queryset_annotation
    def annot_nr_affiliated(self):
        """
        Annotate with the number of affiliated persons, either due to authorship or ProfileAffiliation.
        """
        from profiles.models import Profile

        authors_or_affiliated_counts = (
            Profile.objects.filter(
                Q(affiliations__organization_id=OuterRef("pk"))
                | Q(publicationauthorstable__affiliations__pk=OuterRef("pk"))
            )
            .annotate(_group=Value(1))
            .order_by()
            .values("_group")
            .annotate(total=Count("pk", distinct=True))
            .values("total")[:1]
        )
        return Coalesce(Subquery(authors_or_affiliated_counts), Value(0))

    @queryset_annotation
    def annot_nr_fellows(self):
        """
        Annotate with the number of fellows affiliated with this Organization.
        """
        from colleges.models import Fellowship

        THIS_YEAR = timezone.now().year

        fellowship_counts = (
            Fellowship.objects.filter(
                contributor__profile__affiliations__organization_id=OuterRef("pk")
            )
            .filter(Q(until_date__isnull=True) | Q(until_date__year__gte=THIS_YEAR))
            .order_by()
            .values("contributor__profile__affiliations__organization_id")
            .annotate(total=Count("pk", distinct=True))
            .values("total")[:1]
        )

        return Coalesce(Subquery(fellowship_counts), Value(0))

    @staticmethod
    def get_uncompensated_publications_subquery():
        """
        Return a Subquery which counts the number of uncompensated publications attributed to this Organization.
        """
        return (
            PubFrac.objects.filter(organization_id=OuterRef("pk"))
            .exclude(compensated_by__organization__id=OuterRef("pk"))
            .values("organization_id")
        )

    @queryset_annotation
    def annot_nr_uncompensated_publications(self):
        """
        Annotate with the number of uncompensated publications attributed to this Organization.
        """
        publications_count = (
            self.get_uncompensated_publications_subquery()
            .annotate(total=Count("id"))
            .values("total")[:1]
        )
        return Coalesce(Subquery(publications_count), Value(0))

    @queryset_annotation
    def annot_sum_uncompensated_pubfracs_fraction(self):
        """
        Annotate with the sum of uncompensated PubFracs attributed to this Organization.
        """
        fraction_sum = (
            self.get_uncompensated_publications_subquery()
            .annotate(total=Cast(Sum("fraction"), output_field=FloatField()))
            .values("total")[:1]
        )
        return Coalesce(Subquery(fraction_sum), Value(0.0))

    @queryset_annotation
    def annot_sum_uncompensated_pubfracs_value(self):
        """
        Annotate with the sum of uncompensated PubFracs attributed to this Organization, multiplied by the APEX value.
        """
        value_sum = (
            self.get_uncompensated_publications_subquery()
            .annotate(total=Cast(Sum("cf_value"), output_field=FloatField()))
            .values("total")[:1]
        )
        return Coalesce(Subquery(value_sum), Value(0.0))

    @queryset_annotation
    def annot_sponsorships(self):
        """
        Annotate with the years and amounts in which the Organization has had a subsidy.
        """
        sponsorships = (
            Subsidy.objects.obtained()
            .order_by("date_from__year", "date_until__year")
            .filter(organization_id=OuterRef("pk"))
            .annotate(
                details=JSONObject(
                    amount=F("amount"),
                    year=Coalesce(F("date_from__year"), F("date_until__year")),
                )
            )
            .values("details")
        )
        return ArraySubquery(sponsorships)

    @staticmethod
    def get_balance_value(
        key: str,
        year: int | None = None,
        type: type[float | int] = float,
    ):
        """
        Extract a value from the cf_balance_info JSON field, either for a specific year or cumulatively.
        """
        if year is not None:
            if key in ["subsidy_income", "reserved", "impact_on_reserves"]:
                path = f"cf_balance_info__{year}__{key}"
            else:
                path = f"cf_balance_info__{year}__expenditures__total__{key}"
        else:
            path = f"cf_balance_info__cumulative__{key}"

        if type is float:
            output_field = FloatField()
        elif type is int:
            output_field = IntegerField()
        else:
            raise ValueError(f"Unsupported type: {type}")

        return Coalesce(Cast(F(path), output_field=output_field), Value(0.0))

    @staticmethod
    def get_balance_value_projection(key: str, type: type[float | int] = float):
        """
        Calculate an estimate for the projected value of a metric in the cf_balance_info JSON field, based on the current year's data.
        Returns a tuple of (actual, projected).
        """
        today = timezone.now().date().timetuple()
        actual = OrganizationQuerySet.get_balance_value(key, today.tm_year, type)
        days_in_year = 366 if calendar.isleap(today.tm_year) else 365
        projected = actual / today.tm_yday * days_in_year

        if type is int:
            actual = Cast(Round(actual), output_field=IntegerField())
            projected = Cast(Round(projected), output_field=IntegerField())

        return actual, projected

    def annot_sponsorship_tiers(self):
        """
        Annotate with sponsorship stats and tiers.
        """
        APEX_INFL = 1.10  # 10% inflation
        NAP_INFL = 1.30  # 30% inflation

        # Compensated == Pubfracs (cf_value) covered by own subsidies
        compensated = self.get_balance_value("self_compensated")
        compensated_this_year, _ = self.get_balance_value_projection("self_compensated")
        compensated_past = compensated - compensated_this_year

        # Subsidy Income == sum of subsidies (amount)
        subsidy_income = self.get_balance_value("subsidy_income")
        subsidy_income_this_year, _ = self.get_balance_value_projection(
            "subsidy_income"
        )
        subsidy_income_past = subsidy_income - subsidy_income_this_year

        # Expenditures == sum of pubfracs (cf_value)
        expenditures = self.get_balance_value("expenditures")
        expenditures_this_year, expenditures_proj = self.get_balance_value_projection(
            "expenditures"
        )
        expenditures_past = expenditures - expenditures_this_year

        # Whole Cost == sum of NAP * APEX (equiv to fraction == 1.0)
        # This is also called an "Associated Expenditure" in the cf_balance_info JSON field.
        whole_cost = self.get_balance_value("associated_expenditures")
        whole_cost_this_year, whole_cost_proj = self.get_balance_value_projection(
            "associated_expenditures"
        )
        whole_cost_past = whole_cost - whole_cost_this_year

        prior_debt = expenditures_past - compensated_past  # Pubfracs value
        prior_cost = whole_cost_past - subsidy_income_past  # Total pub cost

        return self.annotate(
            tier_settle=prior_debt,
            tier_replenish=prior_debt / 3 + expenditures_proj,
            tier_cover=prior_debt + expenditures_proj,
            tier_protect=prior_cost + whole_cost_proj * APEX_INFL,
            tier_grow=F("tier_protect") + whole_cost_proj * NAP_INFL * APEX_INFL**2,
        )