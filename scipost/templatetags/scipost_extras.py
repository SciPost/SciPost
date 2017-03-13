from django import template
from django.contrib.auth.models import Group

from scipost.models import Contributor

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
