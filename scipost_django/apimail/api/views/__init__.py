__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .account import EmailAccountListAPIView, UserEmailAccountAccessListAPIView

from .address_book import check_address_book, AddressBookAPIView, AddressBookSelectView

from .attachment import AttachmentFileCreateAPIView

from .event import EventListAPIView, EventRetrieveAPIView

from .tag import UserTagCreateAPIView, UserTagDestroyAPIView, UserTagListAPIView

from .composed_message import (
    ComposedMessageCreateAPIView,
    ComposedMessageUpdateAPIView,
    ComposedMessageDestroyAPIView,
    ComposedMessageListAPIView,
)

from .stored_message import (
    StoredMessageListAPIView,
    StoredMessageRetrieveAPIView,
    StoredMessageUpdateReadAPIView,
    StoredMessageUpdateTagAPIView,
)

from .integrations import mailgun_webhook
