__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.http import HttpResponse


def empty(request):
    return HttpResponse("")
