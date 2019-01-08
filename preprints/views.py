__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import os

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect

from submissions.helpers import check_verified_author
from submissions.models import Submission


def preprint_pdf(request, identifier_w_vn_nr):
    """Open pdf of SciPost preprint or redirect to arXiv page."""
    submission = get_object_or_404(Submission, preprint__identifier_w_vn_nr=identifier_w_vn_nr)
    preprint = submission.preprint

    if preprint.url:
        return redirect(preprint.url)

    # Check if Contributor is author of the Submission
    is_author = check_verified_author(submission, request.user)

    if not submission.visible_public and not is_author:
        if not request.user.is_authenticated:
            raise Http404
        elif not request.user.has_perm(
            'scipost.can_assign_submissions') and not submission.fellows.filter(
                contributor__user=request.user).exists():
                    raise Http404

    __, extension = os.path.splitext(preprint._file.name)
    if extension == '.pdf':
        response = HttpResponse(preprint._file.read(), content_type='application/pdf')
        filename = '{}.pdf'.format(preprint.identifier_w_vn_nr)
        response['Content-Disposition'] = ('filename=' + filename)
    else:
        response = HttpResponse(preprint._file.read(), content_type='application/force-download')
        filename = '{}{}'.format(preprint.identifier_w_vn_nr, extension)
        response['Content-Disposition'] = ('filename=' + filename)
    return response
