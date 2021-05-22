__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models import Q

from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ...models import ValidatedAddress, AddressBookEntry
from ..serializers import (
    AddressBookEntrySerializer, AddressBookEntrySelectSerializer,
    ValidatedAddressSimpleSerializer
)


@api_view(['POST'])
@permission_classes([IsAuthenticated,])
def check_address_book(request):
    """
    For a given email address in POST data, retrieve or create an AddressBookEntry.

    The POST data must contain an 'email' entry.
    """

    if 'email' not in request.data.keys():
        return Response(status=status.HTTP_400_BAD_REQUEST)

    validated_address, address_created = ValidatedAddress.objects.get_or_create(
        address=request.data['email'].lower()
    )
    validated_address.update_mailgun_validation()

    entry, entry_created = AddressBookEntry.objects.get_or_create(
        user=request.user,
        address=validated_address,
    )
    if 'description' in request.data.keys() and request.data['description']:
        entry.description = request.data['description']
        entry.save()
    serializer = ValidatedAddressSimpleSerializer(validated_address)
    return Response(serializer.data)


class AddressBookAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AddressBookEntrySerializer

    def get_queryset(self):
        return self.request.user.address_book_entries.all()


class AddressBookSelectView(ListAPIView):
    """
    Simpler view to feed the vue-select element.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = AddressBookEntrySelectSerializer

    def get_queryset(self):
        queryset = self.request.user.address_book_entries.all()
        query = self.request.query_params.get('q', None)
        if query:
            queryset = queryset.filter(
                Q(address__address__contains=query.lower()) |
                Q(description__icontains=query))
        return queryset
