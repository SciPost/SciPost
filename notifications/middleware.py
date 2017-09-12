class NotificationMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        request.notifications = ['123']
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """ Add notifications in the request if user is logged in! """

        if request.user.is_authenticated:
            request.notifications = request.user.notifications.all()[:5]
            request.notifications_unread = request.user.notifications.unread().count()
