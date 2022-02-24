__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from submissions.models import Submission


class SubmissionPublicSearchAPIFilterSet(df_filters.FilterSet):
    class Meta:
        model = Submission
        fields = {
            "title": ["icontains", "contains", "istartswith", "iregex", "regex"],
            "author_list": ["icontains", "contains", "iregex", "regex"],
            "abstract": ["icontains", "contains", "iregex", "regex"],
            "submission_date": [
                "date__year",
                "date__month",
                "date__exact",
                "date__year__gte",
                "date__year__lte",
                "date__year__range",
                "date__gte",
                "date__lte",
                "date__range",
            ],
            "acad_field__name": [
                "icontains",
            ],
            "specialties__name": [
                "icontains",
            ],
            "topics__name": [
                "icontains",
            ],
        }
