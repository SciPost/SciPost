__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = "affiliates"


urlpatterns = [
    # AffiliateJournals
    path(  # /affiliates/journals
        "journals", views.AffiliateJournalListView.as_view(), name="journals"
    ),
    path(  # /affiliates/journals/<slug>
        "journals/<slug:slug>",
        views.AffiliateJournalDetailView.as_view(),
        name="journal_detail",
    ),
    path(  # /affiliates/journals/<slug>/add_manager
        "journals/<slug:slug>/add_manager",
        views.affiliatejournal_add_manager,
        name="journal_add_manager",
    ),
    path(  # /affiliates/journals/<slug>/remove_manager
        "journals/<slug:slug>/remove_manager/<int:user_id>",
        views.affiliatejournal_remove_manager,
        name="journal_remove_manager",
    ),
    path(  # /affiliates/journals/<slug>/publications/add
        "journals/<slug:slug>/publications/add",
        views.affiliatejournal_add_publication,
        name="journal_add_publication",
    ),
    path(  # /affiliates/journals/<slug>/update_publications_from_Crossref
        "journals/<slug:slug>/update_publications_from_Crossref",
        views.affiliatejournal_update_publications_from_Crossref,
        name="journal_update_publications_from_Crossref",
    ),
    path(  # /affiliates/journals/<slug:slug>/publications/<doi:doi>/pubfractions/add
        "journals/<slug:slug>/publications/<doi:doi>/pubfractions/add",
        views.add_pubfraction,
        name="add_pubfraction",
    ),
    path(  # /affiliates/journals/<slug:slug>/publications/<doi:doi>/pubfractions/<int:pk>/delete
        "journals/<slug:slug>/publications/<doi:doi>/pubfractions/<int:pubfrac_id>/delete",
        views.delete_pubfraction,
        name="delete_pubfraction",
    ),
    # AffiliatePublications
    path(  # /affiliates/publications
        "publications",
        views.AffiliatePublicationListView.as_view(),
        name="publication_list",
    ),
    path(  # /affiliates/publications/<doi:doi>
        "publications/<doi:doi>",
        views.AffiliatePublicationDetailView.as_view(),
        name="publication_detail",
    ),
    # AffiliatePubFractions-related
    path(  # /affiliates/journals/<slug:slug>/organizations
        "journals/<slug:slug>/organizations",
        views.AffiliateJournalOrganizationListView.as_view(),
        name="journal_organizations",
    ),
]
