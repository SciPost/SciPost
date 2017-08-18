# import datetime

from haystack import indexes

from .models import Publication


class PublicationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='title', use_template=True)
    authors = indexes.CharField(model_attr='author_list')
    date = indexes.DateTimeField(model_attr='publication_date')
    abstract = indexes.CharField()
    doi_label = indexes.CharField()

    def get_model(self):
        return Publication

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()
