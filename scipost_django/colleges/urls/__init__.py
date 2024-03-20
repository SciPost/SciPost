__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path, register_converter


from .. import views
from ..converters import CollegeSlugConverter
from ontology.converters import AcademicFieldSlugConverter, SpecialtySlugConverter
from submissions.converters import IdentifierConverter

register_converter(IdentifierConverter, "identifier")
register_converter(CollegeSlugConverter, "college")
register_converter(AcademicFieldSlugConverter, "acad_field")
register_converter(SpecialtySlugConverter, "specialty")


app_name = "colleges"

urlpatterns = [
    # Editorial Colleges: public view
    path("", views.CollegeListView.as_view(), name="colleges"),
    path("<college:college>", views.CollegeDetailView.as_view(), name="college_detail"),
    path(
        "<college:college>/email_Fellows",
        views.email_College_Fellows,
        name="email_College_Fellows",
    ),
    # Fellowships
    path(
        "fellowship-autocomplete",
        views.FellowshipAutocompleteView.as_view(),
        name="fellowship-autocomplete",
    ),
    path(
        "_hx_fellowship_dynsel_list",
        views._hx_fellowship_dynsel_list,
        name="_hx_fellowship_dynsel_list",
    ),
    path(
        "fellowships/<int:contributor_id>/add/",
        views.FellowshipCreateView.as_view(),
        name="fellowship_create",
    ),
    path(
        "fellowships/<int:pk>/update/",
        views.FellowshipUpdateView.as_view(),
        name="fellowship_update",
    ),
    path(
        "fellowships/<int:pk>/",
        views.FellowshipDetailView.as_view(),
        name="fellowship_detail",
    ),
    path(
        "fellowships/<acad_field:acad_field>/<specialty:specialty>",
        views.FellowshipListView.as_view(),
        name="fellowships",
    ),
    path(
        "fellowships/<acad_field:acad_field>",
        views.FellowshipListView.as_view(),
        name="fellowships",
    ),
    path("fellowships", views.FellowshipListView.as_view(), name="fellowships"),
    path(
        "fellowships/<int:pk>/email_start/",
        views.FellowshipStartEmailView.as_view(),
        name="fellowship_email_start",
    ),
    path(
        "submission/<identifier:identifier_w_vn_nr>/fellowship/add",
        views._hx_submission_add_fellowship,
        name="_hx_submission_add_fellowship",
    ),
    path(
        "submission/<identifier:identifier_w_vn_nr>/fellowship/<int:pk>/remove",
        views._hx_submission_remove_fellowship,
        name="_hx_submission_remove_fellowship",
    ),
    path(
        "fellowships/<int:id>/submissions/<identifier:identifier_w_vn_nr>/remove",
        views.fellowship_remove_submission,
        name="fellowship_remove_submission",
    ),
    path(
        "fellowships/<int:id>/submissions/add",
        views.fellowship_add_submission,
        name="fellowship_add_submission",
    ),
    path(
        "fellowships/<int:id>/proceedings/add",
        views.fellowship_add_proceedings,
        name="fellowship_add_proceedings",
    ),
    path(
        "fellowships/<int:id>/proceedings/<int:proceedings_id>/remove",
        views.fellowship_remove_proceedings,
        name="fellowship_remove_proceedings",
    ),
    # Potential Fellowships
    path(
        "potentialfellowships/add/",
        views.PotentialFellowshipCreateView.as_view(),
        name="potential_fellowship_create",
    ),
    path(
        "potentialfellowships/<int:pk>/update/",
        views.PotentialFellowshipUpdateView.as_view(),
        name="potential_fellowship_update",
    ),
    path(
        "potentialfellowsships/<int:pk>/update_status/",
        views.PotentialFellowshipUpdateStatusView.as_view(),
        name="potential_fellowship_update_status",
    ),
    path(
        "potentialfellowships/<int:pk>/delete/",
        views.PotentialFellowshipDeleteView.as_view(),
        name="potential_fellowship_delete",
    ),
    path(
        "potentialfellowships/<int:pk>/events/add/",
        views.PotentialFellowshipEventCreateView.as_view(),
        name="potential_fellowship_event_create",
    ),
    path(
        "potentialfellowships/<int:potfel_id>/vote/<str:vote>/",
        views.vote_on_potential_fellowship,
        name="vote_on_potential_fellowship",
    ),
    path(
        "potentialfellowships/<int:pk>/email_initial/",
        views.PotentialFellowshipInitialEmailView.as_view(),
        name="potential_fellowship_email_initial",
    ),
    path(
        "potentialfellowships/<int:pk>/",
        views.PotentialFellowshipDetailView.as_view(),
        name="potential_fellowship_detail",
    ),
    path(
        "potentialfellowships/<acad_field:acad_field>/<specialty:specialty>",
        views.PotentialFellowshipListView.as_view(),
        name="potential_fellowships",
    ),
    path(
        "potentialfellowships/<acad_field:acad_field>",
        views.PotentialFellowshipListView.as_view(),
        name="potential_fellowships",
    ),
    path(
        "potentialfellowships",
        views.PotentialFellowshipListView.as_view(),
        name="potential_fellowships",
    ),
    ##########################
    # Nominations and Voting #
    ##########################
    path(
        "nominations/",
        include(
            [
                path("", views.nominations, name="nominations"),
                path("_hx_new", views._hx_nomination_new, name="_hx_nomination_new"),
                path(
                    "_hx_new_form/<int:profile_id>",
                    views._hx_nomination_form,
                    name="_hx_nomination_form",
                ),
                path(
                    "search",
                    include(
                        [
                            path(
                                "_hx_form/<str:filter_set>",
                                views._hx_nominations_search_form,
                                name="_hx_nominations_search_form",
                            ),
                            path(
                                "_hx_list",
                                views._hx_nominations_list,
                                name="_hx_nominations_list",
                            ),
                        ]
                    ),
                ),
                path(
                    "<int:nomination_id>/",
                    include(
                        [
                            path(
                                "_hx_round_tab/<int:round_id>",
                                views._hx_nomination_voting_rounds_tab,
                                name="_hx_nomination_voting_rounds_tab",
                            ),
                            path(
                                "_hx_details_contents",
                                views._hx_nomination_details_contents,
                                name="_hx_nomination_details_contents",
                            ),
                            path(
                                "_hx_create_voting_round",
                                views._hx_nomination_voting_rounds_create,
                                name="_hx_nomination_voting_rounds_create",
                            ),
                            path(
                                "_hx_comments",
                                views._hx_nomination_comments,
                                name="_hx_nomination_comments",
                            ),
                            path(
                                "_hx_veto",
                                views._hx_nomination_veto,
                                name="_hx_nomination_veto",
                            ),
                            path(
                                "_hx_delete",
                                views._hx_nomination_delete,
                                name="_hx_nomination_delete",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # Nomination Rounds
    path(
        "nomination_voting_round/<int:round_id>/",
        include(
            [
                path("_hx_vote", views._hx_nomination_vote, name="_hx_nomination_vote"),
                path(
                    "_hx_details",
                    views._hx_voting_round_details,
                    name="_hx_voting_round_details",
                ),
                path(
                    "_hx_voter_table",
                    views._hx_nomination_voter_table,
                    name="_hx_nomination_voter_table",
                ),
                path(
                    "_hx_voting_round_summary",
                    views._hx_voting_round_summary,
                    name="_hx_voting_round_summary",
                ),
                path(
                    "forms/",
                    include(
                        [
                            path(
                                "start_round",
                                views._hx_voting_round_start_form,
                                name="_hx_voting_round_start_form",
                            ),
                            path(
                                "decision",
                                views._hx_nomination_decision_form,
                                name="_hx_nomination_decision_form",
                            ),
                        ]
                    ),
                ),
                # Manage voters of a nomination round
                path(
                    "voters/",
                    include(
                        [
                            path(
                                "<int:fellowship_id>/action/<str:action>",
                                views._hx_nomination_round_eligible_voter_action,
                                name="_hx_nomination_round_eligible_voter_action",
                            ),
                            path(
                                "add_set/<str:voter_set_name>",
                                views._hx_nomination_round_add_eligible_voter_set,
                                name="_hx_nomination_round_add_eligible_voter_set",
                            ),
                        ]
                    ),
                ),
            ],
        ),
    ),
    #######################
    # Fellowships Monitor #
    #######################
    path(
        "fellowships_monitor/",
        include("colleges.urls.fellowships_monitor", namespace="fellowships_monitor"),
    ),
    path(
        "fellowship_invitation/<int:pk>/email_initial",
        views.FellowshipInvitationEmailInitialView.as_view(),
        name="fellowship_invitation_email_initial",
    ),
    path(
        "fellowship_invitation/<int:pk>/email_reminder",
        views.FellowshipInvitationEmailReminderView.as_view(),
        name="fellowship_invitation_email_reminder",
    ),
    path(
        "_hx_fellowship_invitation/<int:invitation_id>/update_response",
        views._hx_fellowship_invitation_update_response,
        name="_hx_fellowship_invitation_update_response",
    ),
]
