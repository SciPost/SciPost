__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from colleges.models import Fellowship


class FellowshipPublicAPIFilterSet(df_filters.FilterSet):
    class Meta:
        model = Fellowship
        fields = {
            "contributor__profile__last_name": [
                "icontains",
                "contains",
                "istartswith",
                "startswith",
            ],
            "contributor__profile__affiliations__organization__country": [
                "icontains",
            ],
            "college__name": [
                "icontains",
            ],
            "start_date": [
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
            "until_date": [
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
