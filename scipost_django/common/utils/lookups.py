__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db.models import Transform


class ImmutableUnaccent(Transform):
    bilateral = True
    lookup_name = "immutable_unaccent"
    function = "IMMUTABLE_UNACCENT"
