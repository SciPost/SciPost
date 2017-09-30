from django import template

from ..constants import subject_areas_dict, subject_areas_raw_dict
from ..models import Contributor

register = template.Library()


#####################
# General utilities #
#####################

@register.filter(name='sort_by')
def sort_by(queryset, order):
    if queryset:
        return queryset.order_by(order)
    return None


@register.filter(name='duration')
def duration(dur):
    total_seconds = int(dur.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return '{}h {}m'.format(hours, minutes)


#######################
# For scipost objects #
#######################

@register.filter(name='is_in_group')
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter(name='associated_contributors')
def associated_contributors(draft):
    return Contributor.objects.filter(
        user__last_name__icontains=draft.last_name)


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


@register.filter(name='get_specialization_code')
def get_specialization_code(code):
    # Get the specialization code without the main subject identifier
    return code.split(':')[1]


@register.filter(name='get_specialization_display')
def get_specialization_display(code):
    # Due to the ArrayField construction, one is not able to use get_FOO_display in the template
    return subject_areas_dict[code]
