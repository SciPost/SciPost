__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime
from django.shortcuts import render

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

    context = {
        "current_sponsors": current_sponsors.order_by_yearly_coverage(year, year),
        "last_year_sponsors": last_year_sponsors.order_by_yearly_coverage(
            year - 1, year - 1
        ),
        "past_sponsors": past_sponsors.order_by_yearly_coverage(None, year - 2),
    }
    return render(request, "sponsors/sponsors.html", context)
