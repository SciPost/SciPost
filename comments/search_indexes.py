__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# import datetime

from haystack import indexes

from .models import Comment


class CommentIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='comment_text', use_template=True)
    authors = indexes.CharField(model_attr='author')
    date = indexes.DateTimeField(model_attr='date_submitted')

    def get_model(self):
        return Comment

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.vetted()
