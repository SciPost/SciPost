__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from .. import views

app_name = "pool"



urlpatterns = [ # building on /submissions/pool/
    path(
        "",
        views.pool,
        name="pool",
    ),
    path( # <identifier>/
        "<identifier:identifier_w_vn_nr>/",
        views.pool,
        name="pool",
    ),
    path(
        "submissions/",
        include([
            path(
                "",
                views.pool_hx_submissions_list,
                name="_hx_submissions_list",
            ),
            path(
                "<identifier:identifier_w_vn_nr>",
                views.pool_hx_submission_li_details,
                name="_hx_submission_li_details",
            ),
        ]),
    ),
    path(
        "add_remark/<identifier:identifier_w_vn_nr>",
        views.add_remark,
        name="add_remark",
    ),
    # Assignment of Editor-in-charge
    path(
        "assignment_request/<int:assignment_id>",
        views.assignment_request,
        name="assignment_request",
    ),
    path(
        "pool/<identifier:identifier_w_vn_nr>/editorial_assignment/",
        include([
            path(
                "",
                views.editorial_assignment,
                name="editorial_assignment",
            ),
            path(
                "<int:assignment_id>/",
                views.editorial_assignment,
                name="editorial_assignment",
            ),
        ]),
    ),
]
