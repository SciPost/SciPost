__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from journals.models import OrgPubFraction
from journals.api.serializers import PublicationPublicSearchSerializer
from organizations.api.serializers import OrganizationPublicSerializer


class PubFractionPublicSerializer(serializers.ModelSerializer):
    organization = OrganizationPublicSerializer(
        fields=["url", "name", "acronym", "country"]
    )
    publication = PublicationPublicSearchSerializer(
        fields=["url", "title", "author_list", "doi_label", "publication_date"]
    )

    class Meta:
        model = OrgPubFraction
        fields = ["organization", "publication", "fraction"]
