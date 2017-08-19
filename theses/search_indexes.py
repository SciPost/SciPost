# import datetime

from haystack import indexes

from .models import ThesisLink


class ThesisIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='title', use_template=True)
    authors = indexes.CharField(model_attr='author')
    supervisor = indexes.CharField(model_attr='supervisor')
    date = indexes.DateTimeField(model_attr='defense_date')
    abstract = indexes.CharField(model_attr='abstract')

    def get_model(self):
        return ThesisLink

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.vetted()
