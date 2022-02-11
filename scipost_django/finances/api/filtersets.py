__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from finances.models import Subsidy


class SubsidyFinAdminAPIFilterSet(df_filters.FilterSet):
    class Meta:
        model = Subsidy
        fields = {
            "organization__name": [
                "icontains",
                "contains",
                "istartswith",
                "iregex",
                "regex",
            ],
            "organization__acronym": [
                "icontains",
                "contains",
                "istartswith",
                "iregex",
                "regex",
            ],
            "organization__country": [
                "icontains",
            ],
            "description": [
                "icontains",
            ],
            "amount": ["gte", "lte", "range"],
            "date": [
                "year",
                "month",
                "exact",
                "year__gte",
                "year__lte",
                "year__range",
                "gte",
                "lte",
                "range",
            ],
            "date_until": [
                "year",
                "month",
                "exact",
                "year__gte",
                "year__lte",
                "year__range",
                "gte",
                "lte",
                "range",
            ],
        }
