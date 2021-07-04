__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view()
@permission_classes([AllowAny,])
def available_search_tabs(request):
    """
    JSON info on Search tabs available for user.
    """
    tabsinfo = [
	{
	    'object_type': 'publication',
	    'label': 'Publications',
	    'url': 'publications'
	},
	{
	    'object_type': 'submission',
	    'label': 'Submissions',
	    'url': 'submissions'
	},
    ]
    if request.user.has_perm('scipost.can_manage_subsidies'):
        tabsinfo.append({
            'object_type': 'subsidy-finadmin',
            'label': 'Subsidies (FinAdmin)',
            'url': 'finadmin/subsidies'
        })
    return Response(tabsinfo)
