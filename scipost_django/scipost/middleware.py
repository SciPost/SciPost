from django.utils.deprecation import MiddlewareMixin


class UsernameHeaderMiddleware(MiddlewareMixin):
    """
    Middleware that adds the username of the user making the request to the response headers.
    Primarily used for pushing the username to the reverse proxy for security logging.
    """

    def process_response(self, request, response):
        response["X-Username"] = request.user.username

        return response
