__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.decorators import protected_resource


@csrf_exempt
@protected_resource()
def userinfo(request):
    """
    Return basic user info, required for using SciPost as OAuth2 authorization server
    """
    user = request.user
    return HttpResponse(
        json.dumps({
            'username': user.username,
            'last_name': user.last_name,
            'first_name': user.first_name,
            'email': user.email
        }),
        content_type='application/json')
