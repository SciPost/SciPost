import os

from django import template


register = template.Library()


@register.filter
def filename(value):
    try:
        return os.path.basename(value.file.name)
    except OSError:
        return 'Error: File not found'
