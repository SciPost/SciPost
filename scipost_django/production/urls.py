__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, re_path, include

from production import views as production_views

app_name = "production"

urlpatterns = [
    # refactoring 2023-05  htmx-driven production page
    path(
        "new",
        production_views.production_new,
        name="production_new",
    ),
    path(
        "_hx_productionstream_list",
        production_views._hx_productionstream_list,
        name="_hx_productionstream_list",
    ),
    # end refactoring 2023-05
    path("", production_views.production, name="production"),
    path("<int:stream_id>", production_views.production, name="production"),
    path("completed", production_views.completed, name="completed"),
    path("officers/new", production_views.user_to_officer, name="user_to_officer"),
    path(
        "officers/<int:officer_id>/delete",
        production_views.delete_officer,
        name="delete_officer",
    ),
    # streams
    path(
        "streams/<int:stream_id>/",
        include(
            [
                path("", production_views.stream, name="stream"),
                path("status", production_views.update_status, name="update_status"),
                path(
                    "proofs/",
                    include(
                        [
                            path(
                                "upload",
                                production_views.upload_proofs,
                                name="upload_proofs",
                            ),
                            path(
                                "<int:version>/",
                                include(
                                    [
                                        path(
                                            "", production_views.proofs, name="proofs"
                                        ),
                                        re_path(
                                            "decision/(?P<decision>accept|decline)$",
                                            production_views.decision,
                                            name="decision",
                                        ),
                                        path(
                                            "send_to_authors",
                                            production_views.send_proofs,
                                            name="send_proofs",
                                        ),
                                        path(
                                            "toggle_access",
                                            production_views.toggle_accessibility,
                                            name="toggle_accessibility",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "<int:attachment_id>/reply/pdf",
                                production_views.production_event_attachment_pdf,
                                name="production_event_attachment_pdf",
                            ),
                        ]
                    ),
                ),
                path("events/add", production_views.add_event, name="add_event"),
                path("logs/add", production_views.add_work_log, name="add_work_log"),
                path("officer/add", production_views.add_officer, name="add_officer"),
                path(
                    "officer/<int:officer_id>/remove",
                    production_views.remove_officer,
                    name="remove_officer",
                ),
                path(
                    "invitations_officer/add",
                    production_views.add_invitations_officer,
                    name="add_invitations_officer",
                ),
                path(
                    "invitations_officer/<int:officer_id>/remove",
                    production_views.remove_invitations_officer,
                    name="remove_invitations_officer",
                ),
                path(
                    "supervisor/add",
                    production_views.add_supervisor,
                    name="add_supervisor",
                ),
                path(
                    "supervisor/<int:officer_id>/remove",
                    production_views.remove_supervisor,
                    name="remove_supervisor",
                ),
                path(
                    "mark_completed",
                    production_views.mark_as_completed,
                    name="mark_as_completed",
                ),
            ]
        ),
    ),
    # events
    path(
        "events/<int:event_id>/",
        include(
            [
                path(
                    "edit",
                    production_views.UpdateEventView.as_view(),
                    name="update_event",
                ),
                path(
                    "delete",
                    production_views.DeleteEventView.as_view(),
                    name="delete_event",
                ),
            ]
        ),
    ),
    # proofs
    path("proofs/<int:slug>", production_views.proofs_pdf, name="proofs_pdf"),
    path(
        "proofs/<int:slug>/decision",
        production_views.author_decision,
        name="author_decision",
    ),
]
