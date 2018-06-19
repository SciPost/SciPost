__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.db.models import Max
from django.utils import timezone

from .models import Preprint


def generate_new_scipost_identifier():
    """Return an identifier for a new SciPost preprint series without version number."""
    now = timezone.now()
    existing_identifier = Preprint.objects.filter(
        created__year=now.year, created__month=now.month).aggregate(
        identifier=Max('scipost_preprint_identifier'))['identifier']
    if not existing_identifier:
        existing_identifier = '1'
    else:
        existing_identifier = str(existing_identifier + 1)
    return '{year}{month}_{identifier}'.format(
        year=now.year, month=str(now.month).rjust(2, '0'),
        identifier=existing_identifier.rjust(5, '0'))


def format_scipost_identifier(identifier, version=1):
    return 'scipost_{identifier}v{version}'.format(
        identifier=identifier, version=version)
