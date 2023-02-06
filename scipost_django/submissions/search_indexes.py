__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


# import datetime

from haystack import indexes

from .models import Submission


class SubmissionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr="title", use_template=True)
    authors = indexes.CharField(model_attr="author_list")
    date = indexes.DateTimeField(model_attr="submission_date")
    abstract = indexes.CharField(model_attr="abstract")

    def get_updated_field(self):
        return "latest_activity"

    def get_model(self):
        return Submission

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.public_latest()
