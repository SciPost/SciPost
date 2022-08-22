__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path, re_path, reverse_lazy
from django.views.generic import TemplateView, RedirectView

from journals import views as journals_views


app_name = "urls.general"


urlpatterns = [
    # Autocomplete
    path(
        "publication-autocomplete",
        journals_views.PublicationAutocompleteView.as_view(),
        name="publication-autocomplete",
    ),
    path(
        "_hx_publication_dynsel_list",
        journals_views._hx_publication_dynsel_list,
        name="_hx_publication_dynsel_list",
    ),
    # Journals
    path("", journals_views.JournalListView.as_view(), name="journals"),
    path(  # patch to preserve old links
        "<acad_field:acad_field>/",
        journals_views.JournalListView.as_view(),
        name="journals_in_acad_spec",
    ),
    path(
        "publications",
        journals_views.PublicationListView.as_view(),
        name="publications",
    ),
    path(
        "scipost_physics",
        RedirectView.as_view(
            url=reverse_lazy("scipost:landing_page", args=["SciPostPhys"])
        ),
    ),
    path(
        "journals_terms_and_conditions",
        TemplateView.as_view(
            template_name="journals/journals_terms_and_conditions.html"
        ),
        name="journals_terms_and_conditions",
    ),
    path(
        "crossmark_policy",
        TemplateView.as_view(template_name="journals/crossmark_policy.html"),
        name="crossmark_policy",
    ),
    # Publication creation
    path(
        "admin/publications/<identifier:identifier_w_vn_nr>/",
        journals_views.DraftPublicationCreateView.as_view(),
        name="create_publication",
    ),
    path(
        "admin/publications/<publication_doi_label:doi_label>/",
        journals_views.DraftPublicationUpdateView.as_view(),
        name="update_publication",
    ),
    path(
        "admin/publications/<publication_doi_label:doi_label>/publish",
        journals_views.PublicationPublishView.as_view(),
        name="publish_publication",
    ),
    path(
        "admin/publications/<publication_doi_label:doi_label>/approval",
        journals_views.DraftPublicationApprovalView.as_view(),
        name="send_publication_for_approval",
    ),
    path(
        "admin/publications/<publication_doi_label:doi_label>/authors",
        journals_views.publication_authors_ordering,
        name="update_author_ordering",
    ),
    path(
        "admin/publications/<publication_doi_label:doi_label>/grants",
        journals_views.PublicationGrantsView.as_view(),
        name="update_grants",
    ),
    path(
        "admin/publications/<publication_doi_label:doi_label>/grants/<int:grant_id>/remove",
        journals_views.PublicationGrantsRemovalView.as_view(),
        name="remove_grant",
    ),
    # Editorial and Administrative Workflow
    path(
        "admin/<publication_doi_label:doi_label>/authors/add",
        journals_views.add_author,
        name="add_author",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/manage_metadata/",
        journals_views.manage_metadata,
        name="manage_metadata",
    ),
    path(
        "admin/manage_metadata/", journals_views.manage_metadata, name="manage_metadata"
    ),
    path(
        "admin/<publication_doi_label:doi_label>/authoraffiliations/",
        journals_views.AuthorAffiliationView.as_view(),
        name="author_affiliations",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/authoraffiliations/<int:pk>/add/",
        journals_views.add_affiliation,
        name="author_affiliation_update",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/authoraffiliations/<int:pk>/remove/<int:organization_id>/",
        journals_views.remove_affiliation,
        name="author_affiliation_remove",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/citation_list_metadata",
        journals_views.CitationUpdateView.as_view(),
        name="create_citation_list_metadata",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/abstract_jats",
        journals_views.AbstractJATSUpdateView.as_view(),
        name="abstract_jats",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/update_references",
        journals_views.update_references,
        name="update_references",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/funders/create_metadata",
        journals_views.FundingInfoView.as_view(),
        name="create_funding_info_metadata",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/funders/add_generic",
        journals_views.add_generic_funder,
        name="add_generic_funder",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/grants/add",
        journals_views.add_associated_grant,
        name="add_associated_grant",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/view_autotemplate/<int:autotemplate_id>/",
        journals_views.view_autogenerated_file,
        name="view_autogenerated_file",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/draft_accompanying_publication",
        journals_views.draft_accompanying_publication,
        name="draft_accompanying_publication",
    ),
    # Admin: Volumes and Issues
    path(
        "admin/volumes/",
        journals_views.VolumesAdminListView.as_view(),
        name="admin_volumes_list",
    ),
    path(
        "admin/volumes/add",
        journals_views.VolumesAdminAddView.as_view(),
        name="add_volume",
    ),
    path(
        "admin/volumes/<int:pk>/",
        journals_views.VolumesAdminUpdateView.as_view(),
        name="update_volume",
    ),
    path(
        "admin/issues/",
        journals_views.IssuesAdminListView.as_view(),
        name="admin_issue_list",
    ),
    path(
        "admin/issues/add",
        journals_views.IssuesAdminAddView.as_view(),
        name="add_issue",
    ),
    path(
        "admin/issues/<int:pk>/",
        journals_views.IssuesAdminUpdateView.as_view(),
        name="update_issue",
    ),
    # Metadata handling
    path(
        "admin/<publication_doi_label:doi_label>/metadata/crossref/create",
        journals_views.CreateMetadataXMLView.as_view(),
        name="create_metadata_xml",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/metadata/crossref/deposit/<str:option>",
        journals_views.metadata_xml_deposit,
        name="metadata_xml_deposit",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/metadata/DOAJ",
        journals_views.produce_metadata_DOAJ,
        name="produce_metadata_DOAJ",
    ),
    path(
        "admin/<publication_doi_label:doi_label>/metadata/DOAJ/deposit",
        journals_views.metadata_DOAJ_deposit,
        name="metadata_DOAJ_deposit",
    ),
    path(
        "admin/metadata/crossref/<int:deposit_id>/mark/<int:success>",
        journals_views.mark_deposit_success,
        name="mark_deposit_success",
    ),
    path(
        "admin/metadata/DOAJ/<int:deposit_id>/mark/<int:success>",
        journals_views.mark_doaj_deposit_success,
        name="mark_doaj_deposit_success",
    ),
    path(
        "admin/metadata/generic/<str:type_of_object>/<int:object_id>/metadata",
        journals_views.generic_metadata_xml_deposit,
        name="generic_metadata_xml_deposit",
    ),
    path(
        "admin/metadata/generic/<int:deposit_id>/mark/<int:success>",
        journals_views.mark_generic_deposit_success,
        name="mark_generic_deposit_success",
    ),
    path(
        "admin/generic/<str:type_of_object>/<int:object_id>/email_made_citable",
        journals_views.email_object_made_citable,
        name="email_object_made_citable",
    ),
    # Topics:
    path(
        "publication_add_topic/<publication_doi_label:doi_label>",
        journals_views.publication_add_topic,
        name="publication_add_topic",
    ),
    path(
        "publication_remove_topic/<publication_doi_label:doi_label>/<slug:slug>/",
        journals_views.publication_remove_topic,
        name="publication_remove_topic",
    ),
    # PubFraction allocation:
    path(
        "allocate_orgpubfractions/<publication_doi_label:doi_label>",
        journals_views.allocate_orgpubfractions,
        name="allocate_orgpubfractions",
    ),
    path(
        "request_pubfrac_check/<publication_doi_label:doi_label>",
        journals_views.request_pubfrac_check,
        name="request_pubfrac_check",
    ),
    # Citedby
    path(
        "admin/citedby/",
        journals_views.harvest_citedby_list,
        name="harvest_citedby_list",
    ),
    path(
        "admin/citedby/<publication_doi_label:doi_label>/harvest",
        journals_views.harvest_citedby_links,
        name="harvest_citedby_links",
    ),
    # Reports
    path(
        "reports/", journals_views.manage_report_metadata, name="manage_report_metadata"
    ),
    path(
        "reports/<int:report_id>/sign",
        journals_views.sign_existing_report,
        name="sign_existing_report",
    ),
    path(
        "reports/<int:report_id>/mark_doi_needed/<int:needed>",
        journals_views.mark_report_doi_needed,
        name="mark_report_doi_needed",
    ),
    # Comments
    path(
        "comments/",
        journals_views.manage_comment_metadata,
        name="manage_comment_metadata",
    ),
    path(
        "comments/<int:comment_id>/mark_doi_needed/<int:needed>",
        journals_views.mark_comment_doi_needed,
        name="mark_comment_doi_needed",
    ),
    # PublicationUpdates
    path(
        "updates/", journals_views.manage_update_metadata, name="manage_update_metadata"
    ),
]
