__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from haystack import indexes

from .models import Publication


class PublicationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr="title", use_template=True)
    authors = indexes.CharField(model_attr="author_list")
    date = indexes.DateTimeField(model_attr="publication_date")
    abstract = indexes.CharField(model_attr="abstract")
    doi_label = indexes.CharField(model_attr="doi_label")

    def get_updated_field(self):
        return "latest_activity"

    def get_model(self):
        return Publication

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.published()
