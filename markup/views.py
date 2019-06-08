__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.http import JsonResponse
from django.shortcuts import render

from markup.forms import MarkupTextForm



def process(request):
    """
    Process the POSTed text.

    This returns a JSON dict containing

    * language
    * processed_markup
    """
    form = MarkupTextForm(request.POST or None)
    if form.is_valid():
        return JsonResponse(form.get_processed_markup())
    return JsonResponse({})
