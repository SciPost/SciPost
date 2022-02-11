__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "funders"

urlpatterns = [
    path(
        "funder-autocomplete",
        views.FunderAutocompleteView.as_view(),
        name="funder-autocomplete",
    ),
    path(
        "grant-autocomplete",
        views.GrantAutocompleteView.as_view(),
        name="grant-autocomplete",
    ),
    path("", views.funders, name="funders"),
    path("dashboard", views.funders_dashboard, name="funders_dashboard"),
    path(
        "query_crossref_for_funder",
        views.query_crossref_for_funder,
        name="query_crossref_for_funder",
    ),
    path("add", views.add_funder, name="add_funder"),
    path("<int:funder_id>/", views.funder_publications, name="funder_publications"),
    path("grants/add", views.CreateGrantView.as_view(), name="add_grant"),
    path(
        "<int:pk>/link_to_organization/",
        views.LinkFunderToOrganizationView.as_view(),
        name="link_to_organization",
    ),
]
