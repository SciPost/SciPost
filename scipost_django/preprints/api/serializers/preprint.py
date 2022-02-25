__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import Preprint


class PreprintPublicSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source="get_absolute_url")

    class Meta:
        model = Preprint
        fields = [
            "identifier_w_vn_nr",
            "url",
        ]
