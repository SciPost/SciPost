__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

import submissions.views.pool.base as views_base
import submissions.views.appraisal as views_appraisal

# app_name = "pool_base"


urlpatterns = [  # building on /submissions/pool/
    path(
        "",
        views_base.pool,
        name="pool",
    ),
    path(  # <identifier>/
        "<identifier:identifier_w_vn_nr>/",
        include(
            [
                path(
                    "",
                    views_base.pool,
                    name="pool",
                ),
                path(
                    "appraisal/",
                    include(
                        [
                            path(
                                "",
                                views_appraisal._hx_appraisal,
                                name="_hx_appraisal",
                            ),
                            path(
                                "qualification_form",
                                views_appraisal._hx_qualification_form,
                                name="_hx_qualification_form",
                            ),
                            path(
                                "readiness_form",
                                views_appraisal._hx_readiness_form,
                                name="_hx_readiness_form",
                            ),
                            path(
                                "radio_form",
                                views_appraisal._hx_radio_appraisal_form,
                                name="_hx_radio_appraisal_form",
                            ),
                        ]
                    ),
                ),
                path(
                    "tab/<slug:tab>",
                    views_base._hx_submission_tab,
                    name="_hx_submission_tab",
                ),
                path(
                    "add_remark",
                    views_base.add_remark,
                    name="add_remark",
                ),
                path(
                    "editorial_assignment/",
                    include(
                        [
                            path(
                                "",
                                views_base.editorial_assignment,
                                name="editorial_assignment",
                            ),
                            path(
                                "<int:assignment_id>/",
                                views_base.editorial_assignment,
                                name="editorial_assignment",
                            ),
                        ]
                    ),
                ),
                path(
                    "manual_EIC_invitation/<int:pk>",
                    views_base.EICManualEICInvitationEmailView.as_view(),
                    name="manual_EIC_invitation",
                ),
            ]
        ),
    ),
    path(
        "submissions/",
        include(
            [
                path(
                    "",
                    views_base.pool_hx_submission_list,
                    name="_hx_submission_list",
                ),
                path(
                    "<identifier:identifier_w_vn_nr>",
                    views_base.pool_hx_submission_details_contents,
                    name="_hx_submission_details_contents",
                ),
            ]
        ),
    ),
    # Assignment of Editor-in-charge
    path(
        "assignment_request/<int:assignment_id>",
        views_base.assignment_request,
        name="assignment_request",
    ),
]
