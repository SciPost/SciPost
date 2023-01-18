__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

import submissions.views.pool as views_pool
import submissions.views.appraisal as views_appraisal

app_name = "pool"


urlpatterns = [ # building on /submissions/pool/
    path(
        "",
        views_pool.pool,
        name="pool",
    ),
    path( # <identifier>/
        "<identifier:identifier_w_vn_nr>/",
        include([
            path(
                "",
                views_pool.pool,
                name="pool",
            ),
            path(
                "appraisal/",
                include([
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
                ]),
            ),
            path(
                "tab/<slug:tab>",
                views_pool._hx_submission_tab,
                name="_hx_submission_tab",
            ),
            path(
                "add_remark",
                views_pool.add_remark,
                name="add_remark",
            ),
            path(
                "editorial_assignment/",
                include([
                    path(
                        "",
                        views_pool.editorial_assignment,
                        name="editorial_assignment",
                    ),
                    path(
                        "<int:assignment_id>/",
                        views_pool.editorial_assignment,
                        name="editorial_assignment",
                    ),
                ]),
            ),
        ])
    ),
    path(
        "submissions/",
        include([
            path(
                "",
                views_pool.pool_hx_submission_list,
                name="_hx_submission_list",
            ),
            path(
                "<identifier:identifier_w_vn_nr>",
                views_pool.pool_hx_submission_details_contents,
                name="_hx_submission_details_contents",
            ),
        ]),
    ),
    # Assignment of Editor-in-charge
    path(
        "assignment_request/<int:assignment_id>",
        views_pool.assignment_request,
        name="assignment_request",
    ),
]
