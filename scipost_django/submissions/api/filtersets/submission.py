__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from submissions.models import Submission


class SubmissionPublicAPIFilterSet(df_filters.FilterSet):
    # FIXME: Displays as [invalid name] on the filter modal
    published = df_filters.BooleanFilter(method="filter_published")
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
            "thread_hash": [
                "istartswith",
                "exact",
            ],
        }

    def filter_published(self, queryset, name, value):
        queryset = queryset.annot_thread_published()
        if value:
            return queryset.filter(thread_published=True)
        else:
            return queryset.filter(thread_published=False)

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
