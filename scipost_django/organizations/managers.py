__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from itertools import chain

from django.contrib.postgres.lookups import Unaccent
from django.db import models
from django.db.models import Q, Exists, OuterRef, Subquery
from django.db.models.functions import Lower
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

from typing import Any, Mapping, TYPE_CHECKING

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
        """
        return Subquery(
            Subsidy.objects.filter(organization=OuterRef("pk"))
            .order_by("-date_from")
            .values("id")[:1]
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
