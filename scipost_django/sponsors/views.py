__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import render

from organizations.models import Organization


def sponsors(request):
    sponsors_20kplus = Organization.objects.with_subsidy_above_and_up_to(20000)
    sponsors_10kplus = Organization.objects.with_subsidy_above_and_up_to(10000, 20000)
    sponsors_5kplus = Organization.objects.with_subsidy_above_and_up_to(5000, 10000)
    current_sponsors = (
        Organization.objects.current_sponsors().with_subsidy_above_and_up_to(0, 5000)
    )
    context = {
        "sponsors_20kplus": sponsors_20kplus,
        "sponsors_10kplus": sponsors_10kplus,
        "sponsors_5kplus": sponsors_5kplus,
        "current_sponsors": current_sponsors.order_by_total_amount_received(),
    }
    return render(request, "sponsors/sponsors.html", context)
