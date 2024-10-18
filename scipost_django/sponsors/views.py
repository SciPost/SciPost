__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from django.db.models import F, Q, Case, Count, OuterRef, Subquery, Value, When
from django.db.models.functions import Extract
from django.shortcuts import render

from finances.models.subsidy import Subsidy
from organizations.models import Organization


def sponsors(request):
    year = datetime.date.today().year

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

    today_year = datetime.date.today().year
    last_sponsorship_counts = dict(
        Organization.objects.annotate(
            last_subsidy_until=Subquery(
                Subsidy.objects.filter(organization=OuterRef("pk"))
                .order_by("-date_until")
                .values("date_until")[:1]
            ),
            years_since_last_subsidy=Extract(F("last_subsidy_until"), "year")
            - today_year,
            last_sponsorship=Case(
                When(
                    Q(years_since_last_subsidy__isnull=True),
                    then=Value("never"),
                ),
                When(
                    Q(years_since_last_subsidy__lte=0),
                    then=Value("current"),
                ),
                When(
                    Q(years_since_last_subsidy=1),
                    then=Value("last_year"),
                ),
                When(
                    Q(years_since_last_subsidy=2),
                    then=Value("2_years_ago"),
                ),
                When(
                    Q(years_since_last_subsidy__gt=2),
                    then=Value("more_than_2_years_ago"),
                ),
            ),
        )
        .values("last_sponsorship")
        .annotate(nr=Count("last_sponsorship"))
        .values_list("last_sponsorship", "nr")
    )
    last_sponsorship_counts["total"] = sum(
        count for k, count in last_sponsorship_counts.items() if k != "never"
    )

    context = {
        "current_sponsors": current_sponsors.order_by_yearly_coverage(year, year),
        "last_year_sponsors": last_year_sponsors.order_by_yearly_coverage(
            year - 1, year - 1
        ),
        "past_sponsors": past_sponsors.order_by_yearly_coverage(None, year - 2),
        "last_sponsorship_counts": last_sponsorship_counts,
    }
    return render(request, "sponsors/sponsors.html", context)
