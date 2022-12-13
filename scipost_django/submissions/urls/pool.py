__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

import submissions.views.pool as views_pool

app_name = "pool"



urlpatterns = [ # building on /submissions/pool/
    path(
        "",
        views_pool.pool,
        name="pool",
    ),
    path( # <identifier>/
        "<identifier:identifier_w_vn_nr>/",
        views_pool.pool,
        name="pool",
    ),
    path(
        "submissions/",
        include([
            path(
                "",
                views_pool.pool_hx_submissions_list,
                name="_hx_submissions_list",
            ),
            path(
                "<identifier:identifier_w_vn_nr>",
                views_pool.pool_hx_submission_details_contents,
                name="_hx_submission_details_contents",
            ),
        ]),
    ),
    path(
        "add_remark/<identifier:identifier_w_vn_nr>",
        views_pool.add_remark,
        name="add_remark",
    ),
    # Assignment of Editor-in-charge
    path(
        "assignment_request/<int:assignment_id>",
        views_pool.assignment_request,
        name="assignment_request",
    ),
    path(
        "pool/<identifier:identifier_w_vn_nr>/editorial_assignment/",
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
]
