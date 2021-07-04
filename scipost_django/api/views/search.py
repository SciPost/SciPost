__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view()
def available_search_tabs(request):
    """
    JSON info on Search tabs available for user.
    """
    tabsinfo = [
	{
	    'objectType': 'publication',
	    'label': 'publications',
	    'url': 'publications'
	},
	{
	    'objectType': 'submission',
	    'label': 'submissions',
	    'url': 'submissions'
	},
    ]
    if request.user.is_authenticated:
        pass
    return Response(tabsinfo)
