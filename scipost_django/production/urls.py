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
    path(
        "productionstreams/<int:productionstream_id>/",
        include(
            [
                path(
                    "details_contents",
                    production_views._hx_productionstream_details_contents,
                    name="_hx_productionstream_details_contents",
                ),
                path(
                    "events/",
                    include(
                        [
                            path(
                                "form",
                                production_views._hx_event_form,
                                name="_hx_event_form",
                            ),
                            path(
                                "<int:event_id>/",
                                include(
                                    [
                                        path(
                                            "update",
                                            production_views._hx_event_form,
                                            name="_hx_event_form",
                                        ),
                                        path(
                                            "delete",
                                            production_views._hx_event_delete,
                                            name="_hx_event_delete",
                                        ),
                                    ]
                                ),
                            ),
                        ]
                    ),
                ),
            ]
        ),
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
                path(
                    "officer",
                    include(
                        [
                            path(
                                "add",
                                production_views.add_officer,
                                name="add_officer",
                            ),
                            path(
                                "<int:officer_id>/remove",
                                production_views.remove_officer,
                                name="remove_officer",
                            ),
                            path(
                                "update",
                                production_views.update_officer,
                                name="update_officer",
                            ),
                        ]
                    ),
                ),
                path(
                    "invitations_officer",
                    include(
                        [
                            path(
                                "add",
                                production_views.add_invitations_officer,
                                name="add_invitations_officer",
                            ),
                            path(
                                "<int:officer_id>/remove",
                                production_views.remove_invitations_officer,
                                name="remove_invitations_officer",
                            ),
                            path(
                                "update",
                                production_views.update_invitations_officer,
                                name="update_invitations_officer",
                            ),
                        ]
                    ),
                ),
                path(
                    "supervisor",
                    include(
                        [
                            path(
                                "add",
                                production_views.add_supervisor,
                                name="add_supervisor",
                            ),
                            path(
                                "<int:officer_id>/remove",
                                production_views.remove_supervisor,
                                name="remove_supervisor",
                            ),
                            path(
                                "update",
                                production_views.update_supervisor,
                                name="update_supervisor",
                            ),
                        ]
                    ),
                ),
                path(
                    "mark_completed",
                    production_views.mark_as_completed,
                    name="mark_as_completed",
                ),
                path(
                    "render_action_buttons/<str:key>",
                    production_views.render_action_buttons,
                    name="render_action_buttons",
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
