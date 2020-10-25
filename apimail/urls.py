__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path
from django.views.generic import TemplateView

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
        path( # /mail/api/attachment_file/create
            'attachment_file/create',
            apiviews.AttachmentFileCreateAPIView.as_view(),
            name='attachment_file_create'
        ),
        path( # /mail/api/composed_message/create
            'composed_message/create',
            apiviews.ComposedMessageCreateAPIView.as_view(),
            name='composed_message_create'
        ),
        path( # /mail/api/composed_message/<uuid>/update
            'composed_message/<uuid:uuid>/update',
            apiviews.ComposedMessageUpdateAPIView.as_view(),
            name='composed_message_update'
        ),
        path( # /mail/api/composed_message/<uuid>/delete
            'composed_message/<uuid:uuid>/delete',
            apiviews.ComposedMessageDestroyAPIView.as_view(),
            name='composed_message_delete'
        ),
        path( # /mail/api/composed_messages
            'composed_messages',
            apiviews.ComposedMessageListAPIView.as_view(),
            name='composed_messages'
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
        path( # /mail/api/stored_message/<uuid>/mark_as_read
            'stored_message/<uuid:uuid>/mark_as_read',
            apiviews.StoredMessageUpdateReadAPIView.as_view(),
            name='api_stored_message_mark_as_read'
        ),
        path( # /mail/api/stored_message/<uuid>/tag
            'stored_message/<uuid:uuid>/tag',
            apiviews.StoredMessageUpdateTagAPIView.as_view(),
            name='api_stored_message_tag'
        ),
        path( # /mail/api/user_tag/create
            'user_tag/create',
            apiviews.UserTagCreateAPIView.as_view(),
            name='user_tag_create'
        ),
        path( # /mail/api/user_tag/<pk>/delete
            'user_tag/<int:pk>/delete',
            apiviews.UserTagDestroyAPIView.as_view(),
            name='user_tag_delete'
        ),
        path( # /mail/api/user_tags
            'user_tags',
            apiviews.UserTagListAPIView.as_view(),
            name='api_user_tags'
        ),
        path( # /mail/api/address_book
            'address_book',
            apiviews.AddressBookAPIView.as_view(),
            name='api_address_book'
        ),
        path( # /mail/api/check_address_book
            'check_address_book',
            apiviews.check_address_book,
            name='api_check_address_book'
        ),
    ])),


    # User views

    path( # /mail/messages
        'messages',
        views.message_list,
        name='message_list'
    ),
    path( # /mail/attachment_file/<uuid>
        'attachment_file/<uuid:uuid>',
        views.attachment_file,
        name='attachment_file'
    ),
]
