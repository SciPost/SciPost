__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import mimetypes

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView

from .models import StoredMessage, StoredMessageAttachment


class StoredMessageListView(ListView):
    model = StoredMessage
    template_name = 'apimail/message_list.html'

    # def get_queryset(self):
    #     return StoredMessage.objects.filter_for_user(self.request.user)


def attachment_file(request, uuid, pk):
    att = get_object_or_404(StoredMessageAttachment,
                            message__uuid=uuid, id=pk)
    content_type, encoding = mimetypes.guess_type(att._file.path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(att._file.read(), content_type=content_type)
    response['Content-Disposition'] = (
        'filename=%s' % att._file.name.rpartition('/')[2])
    response["Content-Encoding"] = encoding
    return response
