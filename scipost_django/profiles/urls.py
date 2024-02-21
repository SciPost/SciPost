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
                    "toggle_verified",
                    views._hx_profile_email_toggle_verified,
                    name="_hx_profile_email_toggle_verified",
                ),
                path(
                    "delete",
                    views._hx_profile_email_delete,
                    name="_hx_profile_email_delete",
                ),
            ]
        ),
    ),
    # Affiliations
    path(
        "<int:profile_id>/affiliation/",
        include(
            [
                path(
                    "add/",
                    views.AffiliationCreateView.as_view(),
                    name="affiliation_create",
                ),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "update/",
                                views.AffiliationUpdateView.as_view(),
                                name="affiliation_update",
                            ),
                            path(
                                "delete/",
                                views.AffiliationDeleteView.as_view(),
                                name="affiliation_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
