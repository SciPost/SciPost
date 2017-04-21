from rest_framework.generics import ListAPIView

from .models import Publication
from .serializers import PublicationSerializer


class PublicationList(ListAPIView):
    """
    List all publications that are published.
    """
    queryset = Publication.objects.published()
    serializer_class = PublicationSerializer
