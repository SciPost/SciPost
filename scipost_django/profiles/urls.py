__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path, include

from . import views

app_name = "profiles"

urlpatterns = [
    # Autocomplete for Select2
    path(
        "profile-autocomplete",
        views.ProfileAutocompleteView.as_view(),
        name="profile-autocomplete",
    ),
    path(
        "autocomplete/dynsel",
        views.HXDynselProfileAutocomplete.as_view(),
        name="profile_dynsel",
    ),
    # Create
    path(
        "add/<from_type>/<int:pk>",
        views.ProfileCreateView.as_view(),
        name="profile_create",
    ),
    path("add/", views.ProfileCreateView.as_view(), name="profile_create"),
    # Match to existing
    path(
        "match/<int:profile_id>/<from_type>/<int:pk>",
        views.profile_match,
        name="profile_match",
    ),
    # List CBV
    path("", views.ProfileListView.as_view(), name="profiles"),
    path(
        "_hx_profile_dynsel_list",
        views._hx_profile_dynsel_list,
        name="_hx_profile_dynsel_list",
    ),
    # Specialties handing via HTMX
    path(
        "_hx_profile_specialties/<int:profile_id>",
        views._hx_profile_specialties,
        name="_hx_profile_specialties",
    ),
    # Instance CBVs
    path(
        "<int:pk>/",
        include(
            [
                path(
                    "send_email/",
                    views.ProfileSendEmailView.as_view(),
                    name="profile_send_email",
                ),
                path(
                    "update/", views.ProfileUpdateView.as_view(), name="profile_update"
                ),
                path(
                    "delete/", views.ProfileDeleteView.as_view(), name="profile_delete"
                ),
                path("", views.ProfileDetailView.as_view(), name="profile_detail"),
            ]
        ),
    ),
    # Duplicates and merging
    path(
        "duplicates/<int:to_merge>/<int:to_merge_into>",
        views.profile_duplicates,
        name="duplicates",
    ),
    path("duplicates/", views.profile_duplicates, name="duplicates"),
    path(
        "_hx_profile_comparison",
        views._hx_profile_comparison,
        name="_hx_profile_comparison",
    ),
    path(
        "_hx_profile_merge/<int:to_merge>/<int:to_merge_into>",
        views._hx_profile_merge,
        name="_hx_profile_merge",
    ),
    path(
        "_hx_profile_merge/",
        views._hx_profile_merge,
        name="_hx_profile_merge",
    ),
    path(
        "_hx_profile_mark_non_duplicate/<int:profile1>/<int:profile2>",
        views._hx_profile_mark_non_duplicate,
        name="_hx_profile_mark_non_duplicate",
    ),
    # Emails
    path(
        "<int:profile_id>/add_email",
        views._hx_add_profile_email,
        name="_hx_add_profile_email",
    ),
    path(
        "emails/<int:email_id>/",
        include(
            [
                path(
                    "delete",
                    views._hx_profile_email_delete,
                    name="_hx_profile_email_delete",
                ),
                path(
                    "make_primary",
                    views._hx_profile_email_mark_primary,
                    name="_hx_profile_email_mark_primary",
                ),
                path(
                    "toggle_valid",
                    views._hx_profile_email_toggle_valid,
                    name="_hx_profile_email_toggle_valid",
                ),
                path(
                    "request_verification",
                    views._hx_profile_email_request_verification,
                    name="_hx_profile_email_request_verification",
                ),
                path(
                    "verify/<str:token>",
                    views.verify_profile_email,
                    name="verify_profile_email",
                ),
            ]
        ),
    ),
    path(
        "<int:profile_id>/",
        include(
            [  # Affiliations
                path(
                    "affiliations/",
                    include(
                        [
                            path(
                                "add",
                                views.AffiliationCreateView.as_view(),
                                name="affiliation_create",
                            ),
                            path(
                                "<int:pk>/update",
                                views.AffiliationUpdateView.as_view(),
                                name="affiliation_update",
                            ),
                            path(
                                "<int:pk>/delete",
                                views.AffiliationDeleteView.as_view(),
                                name="affiliation_delete",
                            ),
                        ]
                    ),
                ),
                # Topic Interests
                path(
                    "topic_interests/",
                    include(
                        [
                            path(
                                "",
                                views.topic_interests,
                                name="topic_interests",
                            ),
                            path(
                                "_hx_formset",
                                views.HXTopicInterestFormSetView.as_view(),
                                name="_hx_topic_interests_formset",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
