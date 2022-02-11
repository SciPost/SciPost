__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.urls import reverse

from ..models import get_profiles as profiles_get_profiles

register = template.Library()


@register.simple_tag
def get_profiles(slug):
    return profiles_get_profiles(slug)


@register.simple_tag(takes_context=True)
def profile_dynsel_action_url(context, profile):
    kwargs = context["action_url_base_kwargs"]
    kwargs["profile_id"] = profile.id
    return reverse(context["action_url_name"], kwargs=kwargs)
