__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ..models import OrgPubFraction
from journals.serializers import PublicationSerializer
from organizations.api.serializers import OrganizationSerializer


class PubFractionSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(
        fields=['url', 'name', 'acronym', 'country']
    )
    publication = PublicationSerializer(
        fields=[
            'url',
            'title', 'author_list',
            'doi_label', 'publication_date'
        ]
    )

    class Meta:
        model = OrgPubFraction
        fields = [
            'organization',
            'publication',
            'fraction'
        ]
