__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer

from colleges.models import Fellowship

from scipost.api.serializers import ContributorPublicAPISerializer

class FellowshipPublicAPISerializer(DynamicFieldsModelSerializer):
    contributor = ContributorPublicAPISerializer()
    college = serializers.StringRelatedField()

    class Meta:
        model = Fellowship
        fields = [
            "contributor",
            "college",
            "start_date",
            "until_date",
            "status",
            "guest",
        ]
