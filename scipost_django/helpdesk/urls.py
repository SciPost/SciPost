__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "helpdesk"

urlpatterns = [
    path("", views.HelpdeskView.as_view(), name="helpdesk"),
    path(
        "queue/<slug:parent_slug>/add/",
        views.QueueCreateView.as_view(),
        name="queue_create",
    ),
    path("queue/add/", views.QueueCreateView.as_view(), name="queue_create"),
    path(
        "queue/<slug:slug>/update/",
        views.QueueUpdateView.as_view(),
        name="queue_update",
    ),
    path(
        "queue/<slug:slug>/delete/",
        views.QueueDeleteView.as_view(),
        name="queue_delete",
    ),
    path("queue/<slug:slug>/", views.QueueDetailView.as_view(), name="queue_detail"),
    path(
        "ticket/add/<int:concerning_type_id>/<int:concerning_object_id>/",
        views.TicketCreateView.as_view(),
        name="ticket_create",
    ),
    path("ticket/add/", views.TicketCreateView.as_view(), name="ticket_create"),
    path(
        "ticket/<int:pk>/update/",
        views.TicketUpdateView.as_view(),
        name="ticket_update",
    ),
    path(
        "ticket/<int:pk>/delete/",
        views.TicketDeleteView.as_view(),
        name="ticket_delete",
    ),
    path(
        "ticket/<int:pk>/assign/",
        views.TicketAssignView.as_view(),
        name="ticket_assign",
    ),
    path("ticket/<int:pk>/", views.TicketDetailView.as_view(), name="ticket_detail"),
    path(
        "ticket/<int:pk>/followup/",
        views.TicketFollowupView.as_view(),
        name="ticket_followup",
    ),
    path(
        "ticket/<int:pk>/resolved/",
        views.TicketMarkResolved.as_view(),
        name="ticket_mark_resolved",
    ),
    path(
        "ticket/<int:pk>/closed/",
        views.TicketMarkClosed.as_view(),
        name="ticket_mark_closed",
    ),
]
