__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from submissions.views.pool import decisionmaking as views

app_name = "decisionmaking"


urlpatterns = [ # building on /submissions/pool/decisionmaking

    path(
        "<identifier:identifier_w_vn_nr>/",
        include([
            path(
                "rec/<int:rec_id>/",
                include([
                    path(
                        "_hx_recommendation_voting_details_contents",
                        views._hx_recommendation_voting_details_contents,
                        name="_hx_recommendation_voting_details_contents",
                    ),
                    path(
                        "voting_rights/grant/",
                        include([
                            path(
                                "spec/<slug:spec_slug>",
                                views._hx_recommendation_grant_voting_right,
                                name="_hx_recommendation_grant_voting_right",
                            ),
                            path(
                                "spec/<slug:spec_slug>/nr/<int:nr>",
                                views._hx_recommendation_grant_voting_right,
                                name="_hx_recommendation_grant_voting_right",
                            ),
                            path(
                                "spec/<slug:spec_slug>/<slug:status>",
                                views._hx_recommendation_grant_voting_right,
                                name="_hx_recommendation_grant_voting_right",
                            ),
                            path(
                                "<int:contributor_id>",
                                views._hx_recommendation_grant_voting_right,
                                name="_hx_recommendation_grant_voting_right",
                            ),
                        ]),
                    ),
                    path(
                        "voting_rights/revoke/",
                        include([
                            path(
                                "<int:contributor_id>",
                                views._hx_recommendation_revoke_voting_right,
                                name="_hx_recommendation_revoke_voting_right",
                            ),
                            path(
                                "<slug:spec_slug>",
                                views._hx_recommendation_revoke_voting_right,
                                name="_hx_recommendation_revoke_voting_right",
                            ),
                        ]),
                    ),
                    path(
                        "open_voting",
                        views._hx_recommendation_open_voting,
                        name="_hx_recommendation_open_voting",
                    ),
                ]),
            ),
        ]),
    ),

]
