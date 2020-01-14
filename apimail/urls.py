__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from apimail.api import views as apiviews
from . import views


app_name = 'apimail'

urlpatterns = [

    # API

    path('api/', include([

        path( # /mail/api/accounts
            'accounts',
            apiviews.EmailAccountListAPIView.as_view(),
            name='accounts'
        ),
        path( # /mail/api/user_account_accesses
            'user_account_accesses',
            apiviews.UserEmailAccountAccessListAPIView.as_view(),
            name='user_account_accesses'
        ),
        path( # /mail/api/events
            'events',
            apiviews.EventListAPIView.as_view(),
            name='api_event_list'
        ),
        path( # /mail/api/event/<uuid>
            'event/<uuid:uuid>',
            apiviews.EventRetrieveAPIView.as_view(),
            name='api_event_retrieve'
        ),
        path( # /mail/api/stored_messages
            'stored_messages',
            apiviews.StoredMessageListAPIView.as_view(),
            name='api_stored_message_list'
        ),
        path( # /mail/api/stored_message/<uuid>
            'stored_message/<uuid:uuid>',
            apiviews.StoredMessageRetrieveAPIView.as_view(),
            name='api_stored_message_retrieve'
        ),
    ])),


    # User views

    path( # /mail/messages
        'messages',
        views.StoredMessageListView.as_view(),
        name='message_list'
    ),
    path( # /mail/message/<uuid>/attachments/<int>
        'message/<uuid:uuid>/attachments/<int:pk>',
        views.attachment_file,
        name='message_attachment'
    ),
]
