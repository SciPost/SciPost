__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "stats"

urlpatterns = [
    path(
        "statistics/<journal_doi_label:journal_doi_label>/<int:volume_nr>/<int:issue_nr>",
        views.statistics,
        name="statistics",
    ),
    path(
        "statistics/<journal_doi_label:journal_doi_label>/<int:volume_nr>",
        views.statistics,
        name="statistics",
    ),
    path("<journal_doi_label:journal_doi_label>", views.statistics, name="statistics"),
    path(
        "statistics/<journal_doi_label:journal_doi_label>/year/<int:year>",
        views.statistics,
        name="statistics",
    ),
    path(
        "country_level_authorships",
        views.country_level_authorships,
        name="country_level_authorships",
    ),
    path(
        "_hx_country_level_authorships/<slug:country>",
        views._hx_country_level_authorships,
        name="_hx_country_level_authorships",
    ),
    path("statistics", views.statistics, name="statistics"),
]
