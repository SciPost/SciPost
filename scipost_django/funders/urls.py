__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path

from . import views

app_name = "funders"

urlpatterns = [
    path(
        "funder-autocomplete",
        views.HXDynselFunderAutocomplete.as_view(),
        name="funder-autocomplete",
    ),
    path(
        "grant-autocomplete",
        views.HXDynselGrantAutocomplete.as_view(),
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
    path(
        "budgets/<int:budget_id>/",
        include(
            [
                path(
                    "",
                    views.IndividualBudgetDetailView.as_view(),
                    name="individual_budget_details",
                ),
                path(
                    "delete/",
                    views.IndividualBudgetDeleteView.as_view(),
                    name="individual_budget_delete",
                ),
                path(
                    "update/",
                    views.IndividualBudgetUpdateView.as_view(),
                    name="individual_budget_update",
                ),
            ]
        ),
    ),
    path(
        "budgets/create/",
        views.IndividualBudgetCreateView.as_view(),
        name="individual_budget_create",
    ),
    path(
        "budgets/",
        views.IndividualBudgetListView.as_view(),
        name="individual_budgets",
    ),
]
