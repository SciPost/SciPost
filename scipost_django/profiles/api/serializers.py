__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer

from profiles.models import Profile, Affiliation

from organizations.api.serializers import OrganizationPublicSerializer


class AffiliationPublicAPISerializer(DynamicFieldsModelSerializer):
    organization = OrganizationPublicSerializer() #serializers.StringRelatedField()

    class Meta:
        model = Affiliation
        fields = [
            "organization",
            "category",
            "date_from",
            "date_until",
        ]


class ProfilePublicAPISerializer(DynamicFieldsModelSerializer):
    title = serializers.CharField(source="get_title_display")
    acad_field = serializers.StringRelatedField()
    specialties = serializers.StringRelatedField(many=True)
    topics = serializers.StringRelatedField(many=True)
    affiliations = AffiliationPublicAPISerializer(many=True)

    class Meta:
        model = Profile
        fields = [
            "title",
            "first_name",
            "last_name",
            "orcid_id",
            "webpage",
            "acad_field",
            "specialties",
            "topics",
            "affiliations",
        ]
