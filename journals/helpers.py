__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import re

from .exceptions import PaperNumberError


def paper_nr_string(nr):
    if nr < 10:
        return '00' + str(nr)
    elif nr < 100:
        return '0' + str(nr)
    elif nr < 1000:
        return str(nr)
    else:
        raise PaperNumberError(nr)
