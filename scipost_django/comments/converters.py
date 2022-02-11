__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


class CommentDOILabelConverter:
    regex = r"^(10.21468/)?SciPost.Comment.[0-9]+"

    def to_python(self, value):
        """Strip the DOI prefix if present; check if Comment exists."""
        doi_label = value
        if doi_label.startswith("10.21468/"):
            doi_label = doi_label.partition("10.21468/")[2]
        from comments.models import Comment

        try:
            return Comment.objects.get(doi_label=doi_label).doi_label
        except Comment.DoesNotExist:
            return ValueError
        return doi_label

    def to_url(self, value):
        return value


class AuthorReplyDOILabelConverter(CommentDOILabelConverter):
    regex = r"^(10.21468/)?SciPost.AuthorReply.[0-9]+"
