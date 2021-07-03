__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer
from ...models import Publication


class PublicationPublicSerializer(DynamicFieldsModelSerializer):
    url = serializers.URLField(source='get_absolute_url')

    class Meta:
        model = Publication
        fields = [
            'title',
            'author_list',
            'abstract',
            'doi_label',
            'publication_date',
            'url'
        ]
