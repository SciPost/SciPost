__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from journals.models import OrgPubFraction


class PubFractionPublicAPIFilterSet(df_filters.FilterSet):
    class Meta:
        model = OrgPubFraction
        fields = {
            "organization__name": ["icontains", "istartswith", "exact"],
            "organization__country": [
                "exact",
            ],
            "publication__publication_date": [
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
            "fraction": ["gte", "lte", "exact"],
        }
