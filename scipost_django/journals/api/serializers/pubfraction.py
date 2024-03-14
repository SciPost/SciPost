__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from finances.models import PubFrac
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
        model = PubFrac
        fields = ["organization", "publication", "fraction"]
