__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template

from ..models import get_profiles as profiles_get_profiles

register = template.Library()


@register.simple_tag
def get_profiles(slug):
    return profiles_get_profiles(slug)
