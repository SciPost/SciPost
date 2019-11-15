__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from apimail.api import views as apiviews
from . import views


app_name = 'apimail'

urlpatterns = [

    # API

    path( # /mail/api/events
        'api/events',
        apiviews.EventListAPIView.as_view(),
        name='api_event_list'
    ),
    path( # /mail/api/event/<uuid>
        'api/event/<uuid:uuid>',
        apiviews.EventRetrieveAPIView.as_view(),
        name='api_event_retrieve'
    ),
    path( # /mail/api/stored_messages
        'api/stored_messages',
        apiviews.StoredMessageListAPIView.as_view(),
        name='api_stored_message_list'
    ),
    path( # /mail/api/stored_message/<uuid>
        'api/stored_message/<uuid:uuid>',
        apiviews.StoredMessageRetrieveAPIView.as_view(),
        name='api_stored_message_retrieve'
    ),


    # User views

    path( # /mail/messages
        'messages',
        views.StoredMessageListView.as_view(),
        name='message_list'
    ),

]
