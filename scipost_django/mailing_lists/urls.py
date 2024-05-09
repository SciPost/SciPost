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
        "<int:mailing_list_id>/newsletters/_hx_create",
        views._hx_newsletter_create,
        name="_hx_newsletter_create",
    ),
    path("newsletters/<int:pk>/edit", views.newsletter_edit, name="newsletter_edit"),
    path(
        "newsletters/<int:pk>/_hx_form",
        views._hx_newsletter_form,
        name="_hx_newsletter_form",
    ),
    path(
        "newsletters/<int:pk>/_hx_media_form",
        views._hx_newsletter_media_form,
        name="_hx_newsletter_media_form",
    ),
    path(
        "newsletters/<int:pk>/_hx_media_embed/list",
        views._hx_newsletter_media_embed_list,
        name="_hx_newsletter_media_embed_list",
    ),
    path(
        "newsletters/<int:pk>/media/<int:media_pk>/_hx_embed",
        views._hx_newsletter_media_embed,
        name="_hx_newsletter_media_embed",
    ),
    path(
        "newsletters/<int:pk>/_hx_display",
        views._hx_newsletter_display,
        name="_hx_newsletter_display",
    ),
    path(
        "newsletters/<int:pk>/_hx_send",
        views._hx_newsletter_send,
        name="_hx_newsletter_send",
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
