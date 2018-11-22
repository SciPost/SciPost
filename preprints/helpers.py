__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models import Max
from django.utils import timezone

from submissions.models import Submission

from .models import Preprint


def generate_new_scipost_identifier(old_preprint=None):
    """Return an identifier for a new SciPost preprint series without version number."""
    now = timezone.now()

    if isinstance(old_preprint, Submission):
        old_preprint = old_preprint.preprint

    if old_preprint:
        # Generate new version number of existing series.
        preprint_series = Preprint.objects.filter(
            scipost_preprint_identifier=old_preprint.scipost_preprint_identifier).values_list(
            'vn_nr', flat=True)
        identifier = '{}v{}'.format(old_preprint.identifier_wo_vn_nr, max(preprint_series) + 1)
        return identifier, old_preprint.scipost_preprint_identifier
    else:
        # New series of Preprints.
        existing_identifier = Preprint.objects.filter(
            created__year=now.year, created__month=now.month).aggregate(
            identifier=Max('scipost_preprint_identifier'))['identifier']
        if not existing_identifier:
            existing_identifier = '1'
        else:
            existing_identifier = str(existing_identifier + 1)

        identifier = '{year}{month}_{identifier}'.format(
            year=now.year, month=str(now.month).rjust(2, '0'),
            identifier=existing_identifier.rjust(5, '0'))
        return identifier, int(existing_identifier)
