__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from . import views

app_name = "mailing_lists"

urlpatterns = [
    path("manage", views.manage, name="manage"),
    path("_hx_create", views._hx_mailing_list_create, name="_hx_mailing_list_create"),
    path("_hx_list", views._hx_mailing_list_list, name="_hx_mailing_list_list"),
    path(
        "<int:pk>/",
        include(
            [
                path(
                    "_hx_toggle_subscription",
                    views._hx_toggle_subscription,
                    name="_hx_toggle_subscription",
                ),
            ]
        ),
    ),
    # Mailchimp
    path(
        "mailchimp/",
        include(
            [
                path("", views.MailchimpListView.as_view(), name="mailchimp_overview"),
                path("sync", views.syncronize_lists, name="sync_mailchimp_lists"),
                path(
                    "sync/<str:list_id>/members",
                    views.syncronize_members,
                    name="sync_mailchimp_members",
                ),
                path(
                    "<str:list_id>/",
                    views.MailchimpListDetailView.as_view(),
                    name="mailchimp_list_detail",
                ),
                path(
                    "non_registered/export",
                    views.export_non_registered_invitations,
                    name="export_non_registered_invitations",
                ),
            ]
        ),
    ),
]
