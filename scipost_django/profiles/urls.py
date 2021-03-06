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
    path("duplicates/", views.ProfileDuplicateListView.as_view(), name="duplicates"),
    path("merge/", views.profile_merge, name="merge"),
    # Emails
    path(
        "<int:profile_id>/add_email", views.add_profile_email, name="add_profile_email"
    ),
    path(
        "emails/<int:email_id>/",
        include(
            [
                path(
                    "make_primary", views.email_make_primary, name="email_make_primary"
                ),
                path("toggle", views.toggle_email_status, name="toggle_email_status"),
                path("delete", views.delete_profile_email, name="delete_profile_email"),
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
