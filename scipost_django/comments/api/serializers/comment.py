__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework import serializers

from ...models import Comment


class CommentPublicSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    author = serializers.SerializerMethodField()
    nested_comments = serializers.SerializerMethodField()
    url = serializers.URLField(source="get_absolute_url")

    class Meta:
        model = Comment
        fields = [
            "status",
            "author",
            "is_author_reply",
            "file_attachment",
            "date_submitted",
            "doi_string",
            "citation",
            "url",
            "nested_comments",
        ]

    def get_author(self, obj):
        return obj.get_author_str()

    def get_nested_comments(self, obj):
        comments = obj.comments.vetted()
        return CommentPublicSerializer(comments, many=True, read_only=True).data
