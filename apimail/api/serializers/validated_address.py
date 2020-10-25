__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import ValidatedAddress, AddressValidation


class AddressValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressValidation
        fields = ['pk', 'data', 'datestamp']


class ValidatedAddressSerializer(serializers.ModelSerializer):
    validations = AddressValidationSerializer(many=True, read_only=True)

    class Meta:
        model = ValidatedAddress
        fields = ['pk', 'address', 'validations']


class ValidatedAddressSimpleSerializer(serializers.ModelSerializer):
    address = serializers.CharField()
    can_send = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta:
        model = ValidatedAddress
        fields = ['address', 'can_send', 'result']

    def get_can_send(self, obj):
        return obj.is_good_for_sending

    def get_result(self, obj):
        return obj.validations.first().data['result']
