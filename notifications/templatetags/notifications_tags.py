# -*- coding: utf-8 -*-
from django.template import Library
from django.utils.html import format_html

register = Library()


@register.assignment_tag(takes_context=True)
def notifications_unread(context):
    user = user_context(context)
    if not user:
        return ''
    return user.notifications.unread().count()


@register.simple_tag(takes_context=True)
def live_notify_badge(context, badge_class='live_notify_badge', classes=''):
    user = user_context(context)
    if not user:
        return ''

    html = "<span class='{badge_class} {classes}' data-count='{unread}'>{unread}</span>".format(
        badge_class=badge_class, unread=user.notifications.unread().count(),
        classes=classes
    )
    return format_html(html)


@register.simple_tag
def live_notify_list(list_class='live_notify_list', classes=''):
    html = "<ul class='{list_class} {classes}'></ul>".format(list_class=list_class,
                                                             classes=classes)
    return format_html(html)


def user_context(context):
    if 'user' not in context:
        return None

    request = context['request']
    user = request.user
    if user.is_anonymous():
        return None
    return user
