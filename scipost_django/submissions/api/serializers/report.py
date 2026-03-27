__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import Report

from comments.api.serializers import CommentPublicSerializer


class ReportPublicSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    url = serializers.URLField(source="get_absolute_url")
    comments = serializers.SerializerMethodField()
    validity = serializers.CharField(source="get_validity_display")
    significance = serializers.CharField(source="get_significance_display")
    originality = serializers.CharField(source="get_originality_display")
    clarity = serializers.CharField(source="get_clarity_display")
    formatting = serializers.CharField(source="get_formatting_display")
    grammar = serializers.CharField(source="get_grammar_display")

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
            "pdf_report",
            "strengths",
            "weaknesses",
            "report",
            "requested_changes",
            "validity",
            "significance",
            "originality",
            "clarity",
            "formatting",
            "grammar",
        ]

    def get_author(self, obj):
        if not obj.anonymous:
            return str(obj.author)
        return "Anonymous"

    def get_comments(self, obj):
        comments = obj.comments.vetted()
        return CommentPublicSerializer(comments, many=True, read_only=True).data
