__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from . import views

app_name = "mailing_lists"

urlpatterns = [
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
]
