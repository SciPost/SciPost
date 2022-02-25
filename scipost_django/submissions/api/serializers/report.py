__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import Report

from comments.api.serializers import CommentPublicSerializer


class ReportPublicSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    url = serializers.URLField(source="get_absolute_url")
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "status",
            "report_type",
            "report_nr",
            "invited",
            "author",
            "doi_string",
            "date_submitted",
            "url",
            "comments",
        ]

    def get_author(self, obj):
        if not obj.anonymous:
            return str(obj.author)
        return "Anonymous"

    def get_comments(self, obj):
        comments = obj.comments.vetted()
        return CommentPublicSerializer(comments, many=True, read_only=True).data
