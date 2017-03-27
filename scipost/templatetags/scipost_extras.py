from django import template
from django.contrib.auth.models import Group

from ..constants import subject_areas_dict
from ..models import Contributor

register = template.Library()


#####################
# General utilities #
#####################

@register.filter(name='sort_by')
def sort_by(queryset, order):
    return queryset.order_by(order)


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


@register.filter(name='reorder_list_three')
def reorder_list_three(ul):
    return ul[::3] + ul[1::3] + ul[2::3]


@register.filter(name='get_specialization_code')
def get_specialization_code(code):
    # Get the specialization code without the main subject identifier
    return code.split(':')[1]


@register.filter(name='get_specialization_display')
def get_specialization_display(code):
    # Due to the ArrayField construction, one is not able to use get_FOO_display in the template
    return subject_areas_dict[code]
