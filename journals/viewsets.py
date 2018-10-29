__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.http import Http404

from rest_framework import viewsets, renderers
from rest_framework.response import Response

from .models import Publication
from .serializers import PublicationSerializerForGoogleScholar


class PublicationViewSetForGoogleScholar(viewsets.ReadOnlyModelViewSet):
    queryset = Publication.objects.published().order_by('-publication_date')
    serializer_class = PublicationSerializerForGoogleScholar
