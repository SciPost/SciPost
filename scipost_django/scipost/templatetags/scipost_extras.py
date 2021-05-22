__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.contrib.contenttypes.models import ContentType

from ..models import Contributor

register = template.Library()


#####################
# General utilities #
#####################

@register.filter(name='list_element')
def list_element(l, idx):
    """Return the element with index idx from list, or None."""
    if type(l) == list:
        try:
            return l[idx]
        except IndexError:
            pass
    return None

@register.filter(name='concatenate')
def concatenate(arg1, arg2):
    """Stringify and concatenate the two arguments"""
    return str(arg1) + str(arg2)


@register.filter(name='sort_by')
def sort_by(queryset, order):
    if queryset:
        return queryset.order_by(order)
    return None


@register.filter(name='duration')
def duration(dur):
    if dur:
        total_seconds = int(dur.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return '{}h {}m'.format(hours, minutes)
    return '0h 0m'


@register.filter(name='content_type_id')
def content_type_id(obj):
    if not obj:
        return None
    return ContentType.objects.get_for_model(obj).id


#######################
# For scipost objects #
#######################

@register.filter(name='is_in_group')
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='associated_contributors')
def associated_contributors(draft):
    return Contributor.objects.filter(
        user__last_name__icontains=draft.last_name).order_by('user__last_name')


def is_modulo(counter, total, modulo):
    q = max(1, int(total / modulo))
    counter -= 1
    return (counter % q) == (q - 1)


@register.filter(name='is_modulo_one_half')
def is_modulo_one_half(counter, total):
    return is_modulo(counter, total, 2)


@register.filter(name='is_modulo_one_third')
def is_modulo_one_third(counter, total):
    return is_modulo(counter, total, 3)
