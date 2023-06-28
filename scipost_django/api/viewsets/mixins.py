__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.decorators import action
from rest_framework.response import Response


class FilteringOptionsActionMixin:
    """
    Mixin for adding the action `filtering_options` to a viewset.
    """

    default_filtering_fields = []

    @action(detail=False)
    def filtering_options(self, request):
        """
        Translate the filterset base filters into list of filtering options.
        """
        advanced_fields_dict = {**self.filterset_class.get_fields()}
        if hasattr(self, "extra_filters"):
            for label, queryspec in self.extra_filters.items():
                advanced_fields_dict[label] = queryspec["lookups"]

        filtering_options = {
            "ordering": self.ordering_fields,
            "basic": [
                field.replace("__", "/").replace("_", " ").title()
                for field in self.search_fields
            ],
            "advanced": [
                {
                    "label": key.replace("__", "/").replace("_", " ").title(),
                    "field": key,
                    "lookups": val,
                }
                for (key, val) in advanced_fields_dict.items()
            ],
        }
        return Response(filtering_options)
