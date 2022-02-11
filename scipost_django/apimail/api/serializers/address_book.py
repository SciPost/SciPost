__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import AddressBookEntry
from ..serializers import ValidatedAddressSerializer


class AddressBookEntrySerializer(serializers.ModelSerializer):
    user = serializers.CharField()
    address = ValidatedAddressSerializer()

    class Meta:
        model = AddressBookEntry
        fields = ["pk", "user", "address", "description"]

    def get_queryset(self):
        user = self.context["request"].user
        return AddressBookEntry.objects.filter(user=user)


class AddressBookEntrySelectSerializer(serializers.ModelSerializer):
    address = serializers.CharField(source="address.address")

    class Meta:
        model = AddressBookEntry
        fields = ["address", "description"]

    def get_queryset(self):
        user = self.context["request"].user
        return AddressBookEntry.objects.filter(user=user)
