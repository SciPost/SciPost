__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import json
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.generic import View

from oauth2_provider.models import get_access_token_model


log = logging.getLogger(__name__)


class UserInfoView(View):
    """
    Self-made userinfo endpoint to enable GitLab OAuth2 sign-in.

    This is a skeletal implementation of an OpenIDConnect userinfo endpoint.

    This view is inspired by `oauth2_provider.views.IntrospectTokenView`.
    """
    required_scopes = ['read']

    @staticmethod
    def get_userinfo_response(token_value=None):
        try:
            token = get_access_token_model().objects.get(token=token_value)
        except ObjectDoesNotExist:
            log.debug("Token not found for token_value %s" % token_value)
            return HttpResponse(
                content=json.dumps({"error": "invalid_token"}),
                status=401,
                content_type="application/json"
            )
        else:
            if token.is_valid():
                data = {
                    "sub": token.user.id,
                    "name": token.user.get_full_name(),
                    "given_name": token.user.get_short_name(),
                    "family_name": token.user.last_name,
                    "preferred_username": token.user.get_username(),
                    "email": token.user.email,
                }
                return HttpResponse(
                    content=json.dumps(data),
                    status=200,
                    content_type="application/json")
            else:
                log.debug("Token %s is invalid" % token_value)
                return HttpResponse(
                    content=json.dumps({"error": "invalid_token"}),
                    status=200,
                    content_type="application/json"
                )

    def get(self, request, *args, **kwargs):
        """
        Get the token from the `Authorization` request header.

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        log.debug(request.headers)
        log.debug(request.body)
        try:
            if request.headers.get("Authorization").startswith("Bearer "):
                token = request.headers.get("Authorization").partition(" ")[2]
                log.debug("GET userinfo, token %s" % token)
            else:
                token = None
                log.debug("GET userinfo, incorrect authorization")
        except AttributeError:
            token = None
        return self.get_userinfo_response(token)
