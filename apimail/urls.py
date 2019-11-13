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
    path( # /apimail/api/stored_messages
        'api/stored_messages',
        views.StoredMessageListAPIView.as_view(),
        name='api_stored_message_list'
    ),
    path( # /apimail/api/stored_message/<uuid>
        'api/stored_message/<uuid:uuid>',
        views.StoredMessageRetrieveAPIView.as_view(),
        name='api_stored_message_retrieve'
    ),
]
