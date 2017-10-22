from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^redirect/(?P<slug>\d+)$', views.forward, name='forward'),
    url(r'^mark-all-as-read/$', views.mark_all_as_read, name='mark_all_as_read'),
    url(r'^mark-toggle/(?P<slug>\d+)/$', views.mark_toggle, name='mark_toggle'),
    url(r'^delete/(?P<slug>\d+)/$', views.delete, name='delete'),
    url(r'^api/unread_count/$', views.live_unread_notification_count,
        name='live_unread_notification_count'),
    url(r'^api/list/$', views.live_notification_list, name='live_unread_notification_list'),
]
