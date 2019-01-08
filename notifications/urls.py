__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^redirect/(?P<slug>\d+)$', views.forward, name='forward'),
    url(r'^mark-toggle/(?P<slug>\d+)/$', views.mark_toggle, name='mark_toggle'),
    url(r'^api/unread_count/$', views.live_unread_notification_count,
        name='live_unread_notification_count'),
    url(r'^api/list/$', views.live_notification_list, name='live_unread_notification_list'),
]
