__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django_filters import rest_framework as df_filters

from organizations.models import Organization


class OrganizationPublicAPIFilterSet(df_filters.FilterSet):
    class Meta:
        model = Organization
        fields = {
            "name": [
                "icontains",
            ],
            "name_original": [
                "icontains",
            ],
            "acronym": [
                "icontains",
            ],
            "country": [
                "exact",
            ],
            "cf_nr_associated_publications": [
                "gte",
                "lte",
            ],
        }
