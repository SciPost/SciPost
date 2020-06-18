__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView, RetrieveAPIView

from django.db.models import Sum

from ..models import Publication, OrgPubFraction
from .serializers import PublicationSerializer, OrgPubFractionSerializer


class PublicationListAPIView(ListAPIView):
    queryset = Publication.objects.published().order_by('-publication_date')
    serializer_class = PublicationSerializer
    lookup_field = 'doi_label'


class PublicationRetrieveAPIView(RetrieveAPIView):
    queryset = Publication.objects.published()
    serializer_class = PublicationSerializer
    lookup_url_kwarg = 'doi_label'
    lookup_field = 'doi_label'


class OrgPubFractionListAPIView(ListAPIView):
    serializer_class = OrgPubFractionSerializer

    def get_queryset(self):
        queryset = OrgPubFraction.objects.all()
        org_id = self.request.query_params.get('org_id', None)
        if org_id is not None:
            queryset = queryset.filter(organization__pk=org_id)
        year = self.request.query_params.get('year', None)
        if year is not None:
            queryset = queryset.filter(publication__publication_date__startswith=year)
        journal = self.request.query_params.get('journal', None)
        if journal is not None:
            queryset = queryset.filter(publication__doi_label__istartswith=journal + '.')
        return queryset
