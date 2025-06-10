__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer

from finances.models import Subsidy, SubsidyPayment
from finances.models.subsidy import SubsidyCollective
from organizations.api.serializers import OrganizationPublicSerializer


class SubsidySerializer(DynamicFieldsModelSerializer):
    url = serializers.URLField(source="get_absolute_url")
    organization = OrganizationPublicSerializer()
    subsidy_type = serializers.CharField(
        source="get_subsidy_type_display", read_only=True
    )

    class Meta:
        model = Subsidy
        fields = [
            "url",
            "organization",
            "subsidy_type",
            "description",
            "amount",
            "amount_publicly_shown",
            "status",
            "date_from",
            "date_until",
            "renewable",
            "renewal_of",
            "collective",
        ]


class SubsidyPaymentSerializer(DynamicFieldsModelSerializer):
    subsidy = SubsidySerializer()

    class Meta:
        model = SubsidyPayment
        fields = [
            "subsidy",
            "amount",
            "date_scheduled",
            "status",
            "invoice_date",
            "payment_date",
        ]


class SubsidyCollectiveSerializer(DynamicFieldsModelSerializer):
    coordinator = OrganizationPublicSerializer()

    class Meta:
        model = SubsidyCollective
        fields = [
            "coordinator",
            "name",
            "description",
            "subsidies",
        ]
