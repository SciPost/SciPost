__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include
from django.views.generic import TemplateView


from . import views

app_name = "forums"

urlpatterns = [
    path(
        "forum/<str:parent_model>/<int:parent_id>/add/",
        views.ForumCreateView.as_view(),
        name="forum_create",
    ),
    path("add/", views.ForumCreateView.as_view(), name="forum_create"),
    path(
        "meeting/<str:parent_model>/<int:parent_id>/add/",
        views.MeetingCreateView.as_view(),
        name="meeting_create",
    ),
    path("meeting/add/", views.MeetingCreateView.as_view(), name="meeting_create"),
    path(
        "<slug:slug>/",
        include([
            path(
                "",
                views.ForumDetailView.as_view(),
                name="forum_detail",
            ),
            path(
                "quicklinks/all",
                views.HX_ForumQuickLinksAllView.as_view(),
                name="_hx_forum_quick_links_all",
            ),
            path(
                "quicklinks/followups",
                views.HX_ForumQuickLinksFollowupsView.as_view(),
                name="_hx_forum_quick_links_followups",
            ),
            path(
                "_hx_thread_from_post/<int:post_id>",
                views._hx_thread_from_post,
                name="_hx_thread_from_post",
            ),
            path(
                "update/",
                views.ForumUpdateView.as_view(),
                name="forum_update",
            ),
            path(
                "delete/",
                views.ForumDeleteView.as_view(),
                name="forum_delete",
            ),
            path(
                "permissions/",
                include([
                    path(
                        "",
                        views.ForumPermissionsView.as_view(),
                        name="forum_permissions",
                    ),
                    path(
                        "<int:group_id>/",
                        views.ForumPermissionsView.as_view(),
                        name="forum_permissions",
                    ),
                    path(
                        "_hx_forum_permissions/",
                        views.HX_ForumPermissionsView.as_view(),
                        name="_hx_forum_permissions",
                    ),
                ]),
            ),
            path(
                (
                    "_hx_post_form/<str:parent_model>/<int:parent_id>/"
                    "<str:origin>/<str:target>/<str:text>/"
                 ),
                include([
                    path(
                        "button",
                        views._hx_post_form_button,
                        name="_hx_post_form_button",
                    ),
                    path(
                        "",
                        views._hx_post_form,
                        name="_hx_post_form",
                    ),
                ]),
            ),
            path(
                "_hx_motion_form/",
                include([
                    path(
                        "button",
                        views._hx_motion_form_button,
                        name="_hx_motion_form_button",
                    ),
                    path(
                        "",
                        views._hx_motion_form,
                        name="_hx_motion_form",
                    ),
                ]),
            ),
        ]),
    ),
    path("", views.ForumListView.as_view(), name="forums"),
    path(
        "<slug:slug>/motion/<int:motion_id>/",
        include([
            path(
                "",
                views._hx_motion_voting,
                name="_hx_motion_voting",
            ),
        ]),
    ),
]
