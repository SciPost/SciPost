# -*- coding: utf-8 -*-
from django.template import Library
from django.template.loader import render_to_string
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

    request = context['request']
    context = {
        'user': user,
    }
    return render_to_string('notifications/partials/notification_list_popover.html',
                            context, request=request)


def user_context(context):
    if 'user' not in context:
        return None

    request = context['request']
    user = request.user
    if user.is_anonymous():
        return None
    return user
