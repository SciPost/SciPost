__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import render

from organizations.models import Organization


def sponsors(request):
    sponsors_20kplus = Organization.objects.with_subsidy_above_and_up_to(20000)
    sponsors_10kplus = Organization.objects.with_subsidy_above_and_up_to(10000, 20000)
    sponsors_5kplus = Organization.objects.with_subsidy_above_and_up_to(5000, 10000)
    current_sponsors = Organization.objects.current_sponsors()
    context = {
        'sponsors_20kplus': sponsors_20kplus,
        'sponsors_10kplus': sponsors_10kplus,
        'sponsors_5kplus': sponsors_5kplus,
        'current_sponsors': current_sponsors,
    }
    return render(request, 'sponsors/sponsors.html', context)
