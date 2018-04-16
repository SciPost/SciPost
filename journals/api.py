__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import ListAPIView

from .models import Publication
from .serializers import PublicationSerializer


class PublicationList(ListAPIView):
    """
    List all publications that are published.
    """
    queryset = Publication.objects.published()
    serializer_class = PublicationSerializer
