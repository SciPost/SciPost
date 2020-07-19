__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models import Max
from django.utils import timezone

from submissions.models import Submission

from .models import Preprint


def get_new_scipost_identifier(thread_hash=None):
    """
    Return an identifier for a new SciPost preprint (consistent with thread history).

    A SciPost identifier is of the form [YYYY][MM]_[#####]v[vn_nr].

    For an existing thread, different cases must be treated:

    * All preprints in thread are SciPost preprints: the vn_nr is incremented.

    * Previous preprints are all on an external preprint server: a brand new SciPost
      identifier is generated; the vn_nr is put to [nr of previous subs in thread] + 1.

    * Previous preprints mix SciPost and external identifiers: the SciPost identifier is
      reused, putting the vn_nr to [nr of previous subs in thread] + 1.
    """
    now = timezone.now()

    submissions_in_thread = Submission.objects.filter(thread_hash=thread_hash)

    scipost_submissions_in_thread = submissions_in_thread.filter(
        preprint__identifier_w_vn_nr__startswith='scipost')

    # At least one previous submission on SciPost's preprint server
    if len(scipost_submissions_in_thread) > 0:
        identifier = '{}v{}'.format(
            scipost_submissions_in_thread.first().identifier_wo_vn_nr,
            str(len(scipost_submissions_in_thread) + 1))
        return identifier

    # No previous Submission, or no previous SciPost preprint in thread; new identifier
    current_identifier_prefix = 'scipost_%s%s' % (now.year, str(now.month).rjust(2,'0'))
    try:
        next_identifier_nr = int(Preprint.objects.filter(
            identifier_w_vn_nr__startswith=current_identifier_prefix
        ).first().identifier_w_vn_nr.rpartition('v')[0].rpartition('_')[2]) + 1
    except AttributeError:
        next_identifier_nr = 1

    identifier = 'scipost_{year}{month}_{identifier}v{vn_nr}'.format(
        year=now.year, month=str(now.month).rjust(2, '0'),
        identifier=str(next_identifier_nr).rjust(5, '0'),
        vn_nr=str(len(submissions_in_thread) + 1)
    )
    return identifier


# def generate_new_scipost_identifier_BUGGED(old_preprint=None):
#     """
#     Return an identifier for a new SciPost preprint series without version number.

#     TODO: This method will explode as soon as it will be used similtaneously by two or more people.
#     """
#     now = timezone.now()

#     if isinstance(old_preprint, Submission):
#         old_preprint = old_preprint.preprint

#     if old_preprint:
#         # Generate new version number of existing series.
#         # BUGGED! This fails to make scipost_preprint_identifier globally unique
#         # BUGGED! Instead, scipost_preprint_identifier can be repeated each month.
#         preprint_series = Preprint.objects.filter(
#             scipost_preprint_identifier=old_preprint.scipost_preprint_identifier).values_list(
#             'vn_nr', flat=True)
#         identifier = '{}v{}'.format(old_preprint.identifier_wo_vn_nr, max(preprint_series) + 1)
#         return identifier, old_preprint.scipost_preprint_identifier
#     else:
#         # New series of Preprints.
#         existing_identifier = Preprint.objects.filter(
#             created__year=now.year, created__month=now.month).aggregate(
#             identifier=Max('scipost_preprint_identifier'))['identifier']
#         if not existing_identifier:
#             existing_identifier = '1'
#         else:
#             existing_identifier = str(existing_identifier + 1)

#         identifier = 'scipost_{year}{month}_{identifier}v1'.format(
#             year=now.year, month=str(now.month).rjust(2, '0'),
#             identifier=existing_identifier.rjust(5, '0'))
#         return identifier, int(existing_identifier)
