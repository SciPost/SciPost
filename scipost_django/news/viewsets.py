__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.http import Http404

from rest_framework import permissions, viewsets, renderers
from rest_framework.response import Response

from .models import NewsItem
from .serializers import NewsItemSerializer


class NewsItemViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny,]
    queryset = NewsItem.objects.homepage().order_by('-date')
    serializer_class = NewsItemSerializer
    template_name = 'news/news_card_content_for_api.html'
    renderer_classes = (renderers.TemplateHTMLRenderer, renderers.JSONRenderer)

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.accepted_renderer.format == 'html':
            return Response({'news': self.get_object()})
        return response

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        if request.accepted_renderer.format == 'html':
            raise Http404
        return response
