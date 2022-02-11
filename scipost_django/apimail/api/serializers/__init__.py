__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from .account import EmailAccountSerializer, EmailAccountAccessSerializer

from .attachment import AttachmentFileSerializer

from .event import EventSerializer

from .tag import UserTagSerializer

from .composed_message import (
    ComposedMessageAPIResponseSerializer,
    ComposedMessageSerializer,
)

from .stored_message import StoredMessageSerializer

from .validated_address import (
    ValidatedAddressSerializer,
    AddressValidationSerializer,
    ValidatedAddressSimpleSerializer,
)

from .address_book import AddressBookEntrySerializer, AddressBookEntrySelectSerializer
