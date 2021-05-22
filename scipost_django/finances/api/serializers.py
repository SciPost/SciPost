__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from organizations.api.serializers import OrganizationSerializer

from ..models import Subsidy


class SubsidySerializer(serializers.ModelSerializer):
    organization = serializers.CharField()#OrganizationSerializer()
    subsidy_type = serializers.CharField(source='get_subsidy_type_display', read_only=True)

    class Meta:
        model = Subsidy
        fields = '__all__'
