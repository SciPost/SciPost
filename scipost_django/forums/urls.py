__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include
from django.views.generic import TemplateView


from . import views

app_name = "forums"

urlpatterns = [
    path("", views.ForumListView.as_view(), name="forums"),
    path(
        "forum/",
        include([
            path(
                "<str:parent_model>/<int:parent_id>/add/",
                views.ForumCreateView.as_view(),
                name="forum_create",
            ),
            path(
                "<slug:slug>/update/",
                views.ForumUpdateView.as_view(),
                name="forum_update",
            ),
            path("add/", views.ForumCreateView.as_view(), name="forum_create"),
        ]),
    ),
    path(
        "meeting/",
        include([
            path(
                "<str:parent_model>/<int:parent_id>/add/",
                views.MeetingCreateView.as_view(),
                name="meeting_create",
            ),
            path(
                "<slug:slug>/update/",
                views.MeetingUpdateView.as_view(),
                name="meeting_update",
            ),
            path("add/", views.MeetingCreateView.as_view(), name="meeting_create"),
        ]),
    ),
    path(
        "<slug:slug>/", # from here on, forum and meeting
        include([
            path(
                "",
                views.ForumDetailView.as_view(),
                name="forum_detail",
            ),
            path(
                "delete/",
                views.ForumDeleteView.as_view(),
                name="forum_delete",
            ),
            path("motions/",
                 include([
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
                     path(
                         "<int:motion_id>/voting",
                         include([
                             path(
                                 "",
                                 views._hx_motion_voting,
                                 name="_hx_motion_voting",
                             ),
                         ]),
                     ),
                 ]),
            ),
            path("posts/",
                 include([
                     path(
                         "_hx_thread_from_post/<int:post_id>",
                         views._hx_thread_from_post,
                         name="_hx_thread_from_post",
                     ),
                 ]),
            ),
            path(
                "quicklinks/",
                include([
                    path(
                        "all",
                        views.HX_ForumQuickLinksAllView.as_view(),
                        name="_hx_forum_quick_links_all",
                    ),
                    path(
                        "followups",
                        views.HX_ForumQuickLinksFollowupsView.as_view(),
                        name="_hx_forum_quick_links_followups",
                    ),
                ]),
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
        ]),
    ),
]
