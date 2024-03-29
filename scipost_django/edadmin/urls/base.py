__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path, register_converter

from ..converters import SubmissionStageSlugConverter
from ..views import base

register_converter(SubmissionStageSlugConverter, "stage")


urlpatterns = [
    path("", base.edadmin, name="edadmin"),
    path(
        "<stage:stage>",
        base._hx_submissions_in_stage,
        name="_hx_submissions_in_stage",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/",
        include(
            [
                path(
                    "details/contents",
                    base._hx_submission_details_contents,
                    name="_hx_submission_details_contents",
                ),
                path(
                    "tab/edadmin",
                    base._hx_submission_tab_contents_edadmin,
                    name="_hx_submission_tab_contents_edadmin",
                ),
            ]
        ),
    ),
]
