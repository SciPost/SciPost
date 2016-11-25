from django import template
from django.contrib.auth.models import Group

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
    group = Group.objects.get(name=group_name)
    return True if group in user.groups.all() else False
