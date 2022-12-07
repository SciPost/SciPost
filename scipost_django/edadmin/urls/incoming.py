__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from ..views import incoming


urlpatterns = [
    path( # "incoming/<identifier>/"
        "<identifier:identifier_w_vn_nr>/",
        include([
            path( # "incoming/<identifier>/admissibility"
                "admissibility",
                incoming._hx_submission_admissibility,
                name="_hx_submission_admissibility",
            ),
            path( # "incoming/<identifier>/plagiarism/"
                "plagiarism/",
                include([
                    path( # "incoming/<identifier>/plagiarism/internal/"
                        "internal/",
                        include([
                            path(
                                "",
                                incoming._hx_plagiarism_internal,
                                name="_hx_plagiarism_internal",
                            ),
                            path(
                                "assess",
                                incoming._hx_plagiarism_internal_assess,
                                name="_hx_plagiarism_internal_assess",
                            ),
                            ]),
                    ), # end "internal/"
                    path( # "incoming/<identifier>/plagiarism/iThenticate/"
                        "iThenticate/",
                        include([
                            path(
                                "",
                                incoming._hx_plagiarism_iThenticate,
                                name="_hx_plagiarism_iThenticate",
                            ),
                            path(
                                "assess",
                                incoming._hx_plagiarism_iThenticate_assess,
                                name="_hx_plagiarism_iThenticate_assess",
                            ),
                        ]),
                    ), # end "iThenticate/"
                ]),
            ), # end "plagiarism/"
            path( # "incoming/<identifier>/admission"
                "admission",
                incoming._hx_submission_admission,
                name="_hx_submission_admission",
            ),
        ])
    ),
]
