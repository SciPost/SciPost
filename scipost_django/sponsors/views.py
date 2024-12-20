__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from django.db.models import F, Q, Case, Count, OuterRef, Subquery, Value, When
from django.db.models.functions import Extract
from django.shortcuts import render
from django.utils import timezone

from finances.models.subsidy import Subsidy
from organizations.models import Organization


def sponsors(request):
    year = timezone.now().year

    current_sponsors = Organization.objects.current_sponsors()
    last_year_sponsors = (
        Organization.objects.all_sponsors()
        .filter(
            subsidy__date_from__year__lte=year - 1,
            subsidy__date_until__year__gte=year - 1,
        )
        .exclude(id__in=current_sponsors.values_list("id", flat=True))
    )
    past_sponsors = (
        Organization.objects.all_sponsors()
        .exclude(id__in=current_sponsors.values_list("id", flat=True))
        .exclude(id__in=last_year_sponsors.values_list("id", flat=True))
    )

    last_sponsorship_counts = dict(
        Organization.objects.annotate(
            last_subsidy_until=Subquery(
                Subsidy.objects.filter(organization=OuterRef("pk"))
                .order_by("-date_until")
                .values("date_until")[:1]
            ),
            last_subsidy_year=Extract(F("last_subsidy_until"), "year"),
            last_sponsorship=Case(
                When(Q(last_subsidy_year__isnull=True), then=Value("never")),
                When(Q(last_subsidy_year__gte=year), then=Value("current")),
                When(Q(last_subsidy_year=year - 1), then=Value("last_year")),
                When(Q(last_subsidy_year=year - 2), then=Value("2_years_ago")),
                When(Q(last_subsidy_year__lt=year - 2), then=Value("gt_2_years_ago")),
            ),
        )
        .values("last_sponsorship")
        .annotate(n=Count("pk", distinct=True))
        .values_list("last_sponsorship", "n")
    )
    last_sponsorship_counts["total"] = sum(
        count for k, count in last_sponsorship_counts.items() if k != "never"
    )

    sponsorships_by_year = {
        y: Subsidy.objects.filter(date_from__year__lte=y, date_until__year__gte=y)
        .order_by("organization_id")
        .distinct("organization_id")
        .count()
        for y in range(year - 3, year + 4)
    }

    context = {
        "current_year": year,
        "current_sponsors": current_sponsors.order_by_yearly_coverage(year, year),
        "last_year_sponsors": last_year_sponsors.order_by_yearly_coverage(
            year - 1, year - 1
        ),
        "past_sponsors": past_sponsors.order_by_yearly_coverage(None, year - 2),
        "last_sponsorship_counts": last_sponsorship_counts,
        "sponsorships_by_year": sponsorships_by_year,
    }
    return render(request, "sponsors/sponsors.html", context)
