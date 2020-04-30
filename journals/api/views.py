__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView, RetrieveAPIView

from ..models import Publication
from .serializers import PublicationSerializer


class PublicationListAPIView(ListAPIView):
    queryset = Publication.objects.published().order_by('-publication_date')
    serializer_class = PublicationSerializer
    lookup_field = 'doi_label'


class PublicationRetrieveAPIView(RetrieveAPIView):
    queryset = Publication.objects.published()
    serializer_class = PublicationSerializer
    lookup_url_kwarg = 'doi_label'
    lookup_field = 'doi_label'
