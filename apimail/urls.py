__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from apimail.api import views


app_name = 'apimail'

urlpatterns = [
    path( # /apimail/api/events
        'api/events',
        views.EventListAPIView.as_view(),
        name='api_event_list'
    ),
    path( # /apimail/api/event/<uuid>
        'api/event/<uuid:uuid>',
        views.EventRetrieveAPIView.as_view(),
        name='api_event_retrieve'
    ),
]
