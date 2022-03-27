__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models import Q

from rest_framework import viewsets


class ExtraFilteredReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        """
        Filter queryset according to `extra_filterset_fields` attribute.
        """
        queryset = super().get_queryset()
        if hasattr(self, "extra_filters"):
            for (label, queryspec) in self.extra_filters.items():
                for lookup in queryspec["lookups"]:
                    param = self.request.query_params.get(
                        "%s__%s" % (label, lookup), None
                    )
                    if param:
                        query = Q()
                        for field in queryspec["fields"]:
                            querydict = {}
                            querydict["%s__%s" % (field, lookup)] = param
                            query = query | Q(**querydict)
                        queryset = queryset.filter(query)
        return queryset.distinct()
