__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .models import Preprint


def preprint_pdf(request, identifier_w_vn_nr):
    """Download the attachment of a Report if available."""
    preprint = get_object_or_404(Preprint, identifier_w_vn_nr=identifier_w_vn_nr, _file__isnull=False)

    response = HttpResponse(preprint._file.read(), content_type='application/pdf')
    filename = '{}_preprint.pdf'.format(preprint.identifier_w_vn_nr)
    response['Content-Disposition'] = ('filename=' + filename)
    return response
