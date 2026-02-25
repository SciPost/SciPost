__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from . import views

app_name = "ethics"


urlpatterns = [
    path(
        "<identifier:identifier_w_vn_nr>/",
        include(
            [
                path(
                    "",
                    views._hx_submission_ethics,
                    name="_hx_submission_ethics",
                ),
                path(
                    "clearance/",
                    include(
                        [
                            path(
                                "assert",
                                views._hx_submission_clearance_assert,
                                name="_hx_submission_clearance_assert",
                            ),
                            path(
                                "revoke",
                                views._hx_submission_clearance_revoke,
                                name="_hx_submission_clearance_revoke",
                            ),
                        ]
                    ),
                ),
                path(
                    "_hx_submission_conflict_of_interest_form",
                    views._hx_submission_conflict_of_interest_form,
                    name="_hx_submission_conflict_of_interest_form",
                ),
                path(
                    "_hx_submission_conflict_of_interest_create/<int:fellowship_id>",
                    views._hx_submission_conflict_of_interest_create,
                    name="_hx_submission_conflict_of_interest_create",
                ),
                path(
                    "_hx_submission_conflict_of_interest_delete/<int:pk>",
                    views._hx_submission_conflict_of_interest_delete,
                    name="_hx_submission_conflict_of_interest_delete",
                ),
                path(
                    "_hx_submission_conflict_of_interest_exemption_toggle/<int:pk>",
                    views._hx_submission_conflict_of_interest_exemption_toggle,
                    name="_hx_submission_conflict_of_interest_exemption_toggle",
                ),
            ],
        ),
    ),
    path(
        "coauthorships/<int:pk>/verify",
        views._hx_coauthorship_verify,
        name="_hx_coauthorship_verify",
    ),
    path(
        "coauthorships/<int:pk>/deprecate",
        views._hx_coauthorship_deprecate,
        name="_hx_coauthorship_deprecate",
    ),
    path(
        "coauthorships/<int:pk>/reset_status",
        views._hx_coauthorship_reset_status,
        name="_hx_coauthorship_reset_status",
    ),
    path(
        "coauthorships/for_submission/<str:identifier_w_vn_nr>/against_profile/<int:profile_pk>/_hx_fetch",
        views._hx_fetch_coauthorships_for_submission_authors,
        name="_hx_fetch_coauthorships_for_submission_authors",
    ),
    path(
        "coauthorships/for_submission/<str:identifier_w_vn_nr>/against_profile/<int:profile_pk>/_hx_list",
        views._hx_list_coauthorships_for_submission_authors,
        name="_hx_list_coauthorships_for_submission_authors",
    ),
    path(
        "conflicts",
        views.conflicts,
        name="conflicts",
    ),
    path(
        "conflicts/_hx_search",
        views.ConflictSearchView.as_view(),
        name="_hx_conflicts_search_form_view",
    ),
]
