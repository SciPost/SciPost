__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from ..views import preassignment

app_name = "preassignment"


urlpatterns = [ # building on /edadmin/preassigmnent/
    path( # <identifier>/
        "<identifier:identifier_w_vn_nr>/",
        include([
            path( # /edadmin/preassignment/<identifier>/author_profiles
                "author_profiles_details_summary",
                preassignment._hx_author_profiles_details_summary,
                name="_hx_author_profiles_details_summary",
            ),
            path( # /edadmin/preassignment/<identifier>/author_profiles
                "author_profiles_details_contents",
                preassignment._hx_author_profiles_details_contents,
                name="_hx_author_profiles_details_contents",
            ),
            path( # /edadmin/preassignment/<identifier>/author_profile_row/<order>
                "author_profile_row/<int:order>",
                preassignment._hx_author_profile_row,
                name="_hx_author_profile_row",
            ),
            path( # /edadmin/preassignment/<identifier>/author_profile_dynsel
                "author_profile_action/<int:order>/<int:profile_id>/<slug:action>",
                preassignment._hx_author_profile_action,
                name="_hx_author_profile_action",
            ),
            path( # /edadmin/preassignment/<identifier>/decision
                "decision",
                preassignment._hx_submission_preassignment_decision,
                name="_hx_submission_preassignment_decision",
            ),
        ])
    ),
]
