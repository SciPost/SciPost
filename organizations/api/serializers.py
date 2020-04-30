__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from django_countries.serializer_fields import CountryField

from ..models import Organization


class OrganizationSerializer(serializers.BaseSerializer):
    name = serializers.CharField(max_length=256)
    name_original = serializers.CharField(max_length=256)
    acronym = serializers.CharField(max_length=64)
    country = CountryField()

    def to_representation(self, instance):
        rep = {
            'name': instance.name,
            'acronym': instance.acronym,
            'country': instance.country.name
        }
        if instance.name_original:
            rep['name_original'] = instance.name_original
        return rep
