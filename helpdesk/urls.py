__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'helpdesk'

urlpatterns = [
    url(
        r'^$',
        views.HelpdeskView.as_view(),
        name='helpdesk'
    ),
    url(
        r'^queue/(?P<parent_slug>[\w-]+)/add/$',
        views.QueueCreateView.as_view(),
        name='queue_create'
    ),
    url(
        r'^queue/add/$',
        views.QueueCreateView.as_view(),
        name='queue_create'
    ),
    url(
        r'^queue/(?P<slug>[\w-]+)/update/$',
        views.QueueUpdateView.as_view(),
        name='queue_update'
    ),
    url(
        r'^queue/(?P<slug>[\w-]+)/delete/$',
        views.QueueDeleteView.as_view(),
        name='queue_delete'
    ),
    url(
        r'^queue/(?P<slug>[\w-]+)/$',
        views.QueueDetailView.as_view(),
        name='queue_detail'
    ),
    url(
        r'^ticket/add/(?P<concerning_type_id>[0-9]+)/(?P<concerning_object_id>[0-9]+)/$',
        views.TicketCreateView.as_view(),
        name='ticket_create'
    ),
    url(
        r'^ticket/add/$',
        views.TicketCreateView.as_view(),
        name='ticket_create'
    ),
    url(
        r'^ticket/(?P<pk>[0-9]+)/update/$',
        views.TicketUpdateView.as_view(),
        name='ticket_update'
    ),
    url(
        r'^ticket/(?P<pk>[0-9]+)/delete/$',
        views.TicketDeleteView.as_view(),
        name='ticket_delete'
    ),
    url(
        r'^ticket/(?P<pk>[0-9]+)/assign/$',
        views.TicketAssignView.as_view(),
        name='ticket_assign'
    ),
    url(
        r'^ticket/(?P<pk>[0-9]+)/$',
        views.TicketDetailView.as_view(),
        name='ticket_detail'
    ),
    url(
        r'^ticket/(?P<pk>[0-9]+)/followup/$',
        views.TicketFollowupView.as_view(),
        name='ticket_followup'
    ),
    url(
        r'^ticket/(?P<pk>[0-9]+)/resolved/$',
        views.TicketMarkResolved.as_view(),
        name='ticket_mark_resolved'
    ),
    url(
        r'^ticket/(?P<pk>[0-9]+)/closed/$',
        views.TicketMarkClosed.as_view(),
        name='ticket_mark_closed'
    ),
]
