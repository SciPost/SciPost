__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer

from organizations.models import Organization


class OrganizationPublicSerializer(DynamicFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="organizations:organization_detail", lookup_field="pk"
    )

    class Meta:
        model = Organization
        fields = [
            "url",
            "orgtype",
            "status",
            "name",
            "name_original",
            "acronym",
            "country",
            "parent",
            "superseded_by",
        ]


class OrganizationNAPSerializer(OrganizationPublicSerializer):
    nap = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "url",
            "orgtype",
            "status",
            "name",
            "name_original",
            "acronym",
            "country",
            "parent",
            "superseded_by",
            "nap",
        ]

    def get_nap(self, obj):
        per_year = {}
        for year in range(datetime.date.today().year, 2015, -1):
            per_year[year] = obj.get_publications(year=year).count()
        return {"total": obj.cf_nr_associated_publications, "per_year": per_year}


class OrganizationBalanceSerializer(serializers.BaseSerializer):
    def to_representation(self, instance):
        return instance.get_balance_info()
