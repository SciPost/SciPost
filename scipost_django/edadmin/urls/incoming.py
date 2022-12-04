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
                "_hx_plagiarism_internal",
                incoming._hx_plagiarism_internal,
                name="_hx_plagiarism_internal",
            ),
            path(
                "_hx_plagiarism_iThenticate",
                incoming._hx_plagiarism_iThenticate,
                name="_hx_plagiarism_iThenticate",
            ),
        ])
    ),
]
