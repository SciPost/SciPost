__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.shortcuts import render

from organizations.models import Organization


def sponsors(request):
    current_sponsors = Organization.objects.current_sponsors()
    context = {
        'current_sponsors': current_sponsors,
    }
    return render(request, 'sponsors/sponsors.html', context)
