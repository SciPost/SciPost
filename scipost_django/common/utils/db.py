__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.db.models import Func


class SplitString(Func):
    function = "regexp_split_to_array"
    template = "%(function)s(%(expressions)s, '%(delimiter)s')"
    arg_joiner = ", "
