# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.template import Library
from django.utils.html import format_html

register = Library()


@register.simple_tag(takes_context=True)
def live_notify_badge(context, classes=''):
    html = "<span class='live_notify_badge {classes}'>0</span>".format(classes=classes)
    return format_html(html)


@register.simple_tag(takes_context=True)
def live_notify_list(context):
    user = user_context(context)
    if not user:
        return ''

    html = '<div class="dropdown-menu notifications">'

    # User default links
    html += '<h6 class="dropdown-header">Welcome {first_name} {last_name}</h6>'.format(
        first_name=user.first_name, last_name=user.last_name)

    if hasattr(user, 'contributor'):
        html += '<a class="dropdown-item" href="{url}">Personal Page</a>'.format(
            url=reverse('scipost:personal_page'))

    # User specific links
    if user.has_perm('scipost.can_read_partner_page'):
        html += '<a class="dropdown-item" href="{url}">Partner Page</a>'.format(
            url=reverse('partners:dashboard'))
    if user.has_perm('scipost.can_view_timesheets'):
        html += '<a class="dropdown-item" href="{url}">Financial Administration</a>'.format(
            url=reverse('finances:finance'))
    if user.has_perm('scipost.can_view_production'):
        html += '<a class="dropdown-item" href="{url}">Production</a>'.format(
            url=reverse('production:production'))
    if user.has_perm('scipost.can_view_pool'):
        html += '<a class="dropdown-item" href="{url}">Submission Pool</a>'.format(
            url=reverse('submissions:pool'))

    # Logout links
    html += '<div class="dropdown-divider my-0"></div>'
    html += '<a class="dropdown-item" href="{url}">Logout</a>'.format(
        url=reverse('scipost:logout'))

    # Notifications
    html += '<div class="dropdown-divider my-0"></div><h6 class="dropdown-header">Inbox</h6>'
    html += '<div class="live_notify_list"></div></div>'
    return format_html(html)


def user_context(context):
    if 'user' not in context:
        return None

    request = context['request']
    user = request.user
    if user.is_anonymous():
        return None
    return user
