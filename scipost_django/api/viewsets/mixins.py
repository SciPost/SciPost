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
        filtering_options = {
            'basic': [
                field.replace('__', ':').replace('_', ' ').title() for field in self.search_fields
            ],
            'advanced': [
                {
                    'label': key.rpartition('__')[0].replace('__', ':').replace('_', ' ').title(),
                    'field': key.rpartition('__')[0],
                    'lookup': key.rpartition('__')[2],
                    'default': key in self.default_filtering_fields
                } for key in self.filterset_class.base_filters.keys()
            ]
        }
        return Response(filtering_options)
