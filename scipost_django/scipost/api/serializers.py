__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer

from scipost.models import Contributor

from profiles.api.serializers import ProfilePublicAPISerializer


class ContributorPublicAPISerializer(DynamicFieldsModelSerializer):
    profile = ProfilePublicAPISerializer()

    class Meta:
        model = Contributor
        fields = [
            "profile",
        ]
