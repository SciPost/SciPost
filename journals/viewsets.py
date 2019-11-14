__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.http import Http404

from rest_framework import permissions, viewsets, renderers
from rest_framework.response import Response

from .models import Publication
from .serializers import PublicationSerializerForGoogleScholar


class PublicationViewSetForGoogleScholar(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny,]
    queryset = Publication.objects.published().order_by('-publication_date')
    serializer_class = PublicationSerializerForGoogleScholar
