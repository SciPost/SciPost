__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..utils import process_markup


register = template.Library()


@register.filter(name='automarkup')
def automarkup(text, language_forced=None):
    return process_markup(text, language_forced=language_forced)['processed']
