__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# import datetime

from haystack import indexes

from .models import Commentary


class CommentaryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='title', use_template=True)
    authors = indexes.CharField(model_attr='author_list')
    date = indexes.DateTimeField(model_attr='pub_date', null=True)
    abstract = indexes.CharField(model_attr='pub_abstract')

    def get_model(self):
        return Commentary

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.vetted()
