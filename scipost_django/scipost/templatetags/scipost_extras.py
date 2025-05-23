__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from functools import reduce
import random

from django import template
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from ..models import Contributor

register = template.Library()


#####################
# General utilities #
#####################


@register.filter(name="list_element")
def list_element(l, idx):
    """Return the element with index idx from list, or None."""
    if type(l) == list:
        try:
            return l[idx]
        except IndexError:
            pass
    return None


@register.filter(name="concatenate")
def concatenate(arg1, arg2):
    """Stringify and concatenate the two arguments"""
    return str(arg1) + str(arg2)


@register.filter(name="sort_by")
def sort_by(queryset, order):
    if queryset:
        return queryset.order_by(order)
    return None


@register.filter(name="duration")
def duration(dur):
    if dur:
        total_seconds = int(dur.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return "{}h {}m".format(hours, minutes)
    return "0h 0m"


@register.filter(name="content_type_id")
def content_type_id(obj):
    if not obj:
        return None
    return ContentType.objects.get_for_model(obj).id


@register.filter
def object_name(obj):
    import re

    if obj is None:
        return None
    else:
        # Add spaces before capital letters in the object name to make it more readable
        return re.sub(r"([^\s])([A-Z])", r"\1 \2", obj._meta.object_name)


@register.filter(name="get_fields")
def get_fields(obj):
    return obj._meta.get_fields()


@register.filter(name="get_field_value")
def get_field_value(obj, field_name):
    return getattr(obj, field_name)


@register.filter
def get_admin_url(obj):
    return reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=(obj.pk,)
    )


@register.filter(name="increment_dt")
def increment_dt(dt):
    try:
        delta = abs(int(dt))
        if delta >= 8:
            return random.randint(delta, int(1.4 * delta))
    except:
        pass
    return random.randint(8, 12)


#######################
# For scipost objects #
#######################


@register.filter(name="is_in_group")
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name="associated_contributors")
def associated_contributors(draft):
    return Contributor.objects.filter(
        dbuser__last_name__icontains=draft.last_name
    ).order_by("dbuser__last_name")


@register.filter
def readable_str(value):
    replacements = {
        "_": " ",
    }
    return reduce(lambda a, kv: a.replace(*kv), replacements.items(), value)


@register.filter
def all_fields_have_choices(form):
    for field in form.fields:
        if len(form.fields[field].choices) == 0:
            return False
    return True
