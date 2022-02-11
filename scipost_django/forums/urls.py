__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

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
    path("<slug:slug>/", views.ForumDetailView.as_view(), name="forum_detail"),
    path("<slug:slug>/update/", views.ForumUpdateView.as_view(), name="forum_update"),
    path("<slug:slug>/delete/", views.ForumDeleteView.as_view(), name="forum_delete"),
    path(
        "<slug:slug>/permissions/<int:group_id>/",
        views.ForumPermissionsView.as_view(),
        name="forum_permissions",
    ),
    path(
        "<slug:slug>/permissions/",
        views.ForumPermissionsView.as_view(),
        name="forum_permissions",
    ),
    path("", views.ForumListView.as_view(), name="forums"),
    path(
        "<slug:slug>/post/<str:parent_model>/<int:parent_id>/add/",
        views.PostCreateView.as_view(),
        name="post_create",
    ),
    path(
        "<slug:slug>/motion/<str:parent_model>/<int:parent_id>/add/",
        views.MotionCreateView.as_view(),
        name="motion_create",
    ),
    path(
        "<slug:slug>/post/<str:parent_model>/<int:parent_id>/add/confirm/",
        views.PostConfirmCreateView.as_view(),
        name="post_confirm_create",
    ),
    path(
        "<slug:slug>/motion/<str:parent_model>/<int:parent_id>/add/confirm/",
        views.MotionConfirmCreateView.as_view(),
        name="motion_confirm_create",
    ),
    path(
        "<slug:slug>/motion/<int:motion_id>/<str:vote>/",
        views.motion_vote,
        name="motion_vote",
    ),
]
