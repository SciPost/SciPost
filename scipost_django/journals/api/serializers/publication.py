__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from api.serializers import DynamicFieldsModelSerializer
from ...models import Publication


class PublicationPublicSerializer(DynamicFieldsModelSerializer):
    url = serializers.URLField(source="get_absolute_url")
    doi = serializers.URLField(source="doi_string")
    accepted_submission = serializers.SerializerMethodField()
    acad_field = serializers.StringRelatedField()
    specialties = serializers.StringRelatedField(many=True)
    topics = serializers.StringRelatedField(many=True)
    approaches = serializers.StringRelatedField()

    class Meta:
        model = Publication
        fields = [
            "url",
            "title",
            "author_list",
            "abstract",
            "doi_label",
            "doi",
            "submission_date",
            "acceptance_date",
            "publication_date",
            "cc_license",
            "accepted_submission",
            "acad_field",
            "specialties",
            "topics",
            "approaches",
        ]

    def get_accepted_submission(self, obj):
        return obj.accepted_submission.get_absolute_url()


class PublicationPublicSearchSerializer(DynamicFieldsModelSerializer):
    url = serializers.URLField(source="get_absolute_url")

    class Meta:
        model = Publication
        fields = [
            "url",
            "title",
            "author_list",
            "abstract",
            "doi_label",
            "publication_date",
        ]
