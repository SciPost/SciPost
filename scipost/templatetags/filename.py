__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import os

from django import template


register = template.Library()


@register.filter
def filename(value):
    try:
        return os.path.basename(value.file.name)
    except OSError:
        return 'Error: File not found'
