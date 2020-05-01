__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from django_countries.serializer_fields import CountryField

from ..models import Organization

from journals.api.serializers import OrgPubFractionSerializer



class OrganizationSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Organization
        fields = [
            'name', 'name_original', 'acronym', 'country'
        ]
        read_only_fields = [
            'name', 'name_original', 'acronym', 'country'
        ]
