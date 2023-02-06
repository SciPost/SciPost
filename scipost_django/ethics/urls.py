__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from . import views

app_name = "ethics"


urlpatterns = [
    path(
        "<identifier:identifier_w_vn_nr>/",
        include([
            path(
                "",
                views._hx_submission_ethics,
                name="_hx_submission_ethics",
            ),
            path(
                "clearance/",
                include([
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
                ]),
            ),
            path(
                "_hx_submission_competing_interest_form",
                views._hx_submission_competing_interest_form,
                name="_hx_submission_competing_interest_form",
            ),
            path(
                "_hx_submission_competing_interest_delete/<int:pk>",
                views._hx_submission_competing_interest_delete,
                name="_hx_submission_competing_interest_delete",
            ),
        ]),
    ),
]
