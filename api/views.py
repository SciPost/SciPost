__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.decorators import protected_resource

log = logging.getLogger(__name__)


@csrf_exempt
@protected_resource()
def userinfo(request):
    """
    Return basic user info, required for using SciPost as OAuth2 authorization server
    """
    log.debug(request.headers)
    log.debug(request.META)
    log.debug(request.GET)
    log.debug(request.user)
    log.debug(request.user.is_authenticated)
    user = request.user
    return HttpResponse(
        json.dumps({
            'provider': 'SciPost',
            'uid': user.id,
            'username': user.username,
            'name': ("%s %s" % (user.first_name, user.last_name)),
            'last_name': user.last_name,
            'first_name': user.first_name,
            'email': user.email
        }),
        content_type='application/json')
