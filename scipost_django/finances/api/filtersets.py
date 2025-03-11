__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from finances.models import Subsidy, SubsidyPayment


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
            "date_from": [
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


class SubsidyPaymentAPIFilterSet(df_filters.FilterSet):
    class Meta:
        model = SubsidyPayment
        fields = {
            "subsidy__organization__name": [
                "icontains",
                "contains",
                "istartswith",
                "iregex",
                "regex",
            ],
            "subsidy__organization__acronym": [
                "icontains",
                "contains",
                "istartswith",
                "iregex",
                "regex",
            ],
            "subsidy__organization__country": [
                "icontains",
            ],
            "subsidy__description": [
                "icontains",
            ],
            "subsidy__amount": ["gte", "lte", "range"],
            "subsidy__date_from": [
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
            "subsidy__date_until": [
                "year",
                "exact",
                "year__gte",
                "year__lte",
                "year__range",
                "gte",
                "lte",
                "range",
            ],
            "invoice__date": [
                "year",
                "exact",
                "year__gte",
                "year__lte",
                "year__range",
                "gte",
                "lte",
                "range",
            ],
            "proof_of_payment__date": [
                "year",
                "exact",
                "year__gte",
                "year__lte",
                "year__range",
                "gte",
                "lte",
                "range",
            ],
            "date_scheduled": [
                "year",
                "exact",
                "year__gte",
                "year__lte",
                "year__range",
                "gte",
                "lte",
                "range",
            ],
            "amount": ["gte", "lte", "range"],
        }
