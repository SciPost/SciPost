__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from ..views import incoming


urlpatterns = [
    path(
        "_hx_incoming_list",
        incoming._hx_incoming_list,
        name="_hx_incoming_list",
    ),
    path(
        "<identifier:identifier_w_vn_nr>/",
        include([
            path(
                "_hx_submission_admissibility",
                incoming._hx_submission_admissibility,
                name="_hx_submission_admissibility",
            ),
            path(
                "_hx_submission_details_contents",
                incoming._hx_submission_details_contents,
                name="_hx_submission_details_contents",
            ),
            path(
                "_hx_plagiarism_internal",
                incoming._hx_plagiarism_internal,
                name="_hx_plagiarism_internal",
            ),
            path(
                "_hx_plagiarism_internal_assess",
                incoming._hx_plagiarism_internal_assess,
                name="_hx_plagiarism_internal_assess",
            ),
            path(
                "_hx_plagiarism_iThenticate",
                incoming._hx_plagiarism_iThenticate,
                name="_hx_plagiarism_iThenticate",
            ),
            path(
                "_hx_plagiarism_iThenticate_assess",
                incoming._hx_plagiarism_iThenticate_assess,
                name="_hx_plagiarism_iThenticate_assess",
            ),
            path(
                "_hx_submission_admission",
                incoming._hx_submission_admission,
                name="_hx_submission_admission",
            ),
        ])
    ),
]
