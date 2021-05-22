__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import mimetypes

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import AttachmentFile


@login_required
def mail(request):
    return render(request, 'apimail/mail.html')


@login_required
def attachment_file(request, uuid):
    """
    Return an attachment file.
    """
    att = get_object_or_404(AttachmentFile, uuid=uuid)
    content_type, encoding = mimetypes.guess_type(att.file.path)
    content_type = content_type or 'application/octet-stream'
    response = HttpResponse(att.file.read(), content_type=content_type)
    response['Content-Disposition'] = (
        'filename=%s' % att.file.name.rpartition('/')[2])
    response["Content-Encoding"] = encoding
    return response
