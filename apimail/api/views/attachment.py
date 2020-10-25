__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from ...models import AttachmentFile
from ..serializers import AttachmentFileSerializer


class AttachmentFileCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = AttachmentFile.objects.all()
    serializer_class = AttachmentFileSerializer
    parser_classes = [FormParser, MultiPartParser,]
