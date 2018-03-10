from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from submissions.constants import SUBMISSIONS_COMPLETE_REGEX

from journals.constants import PUBLICATION_DOI_REGEX, REGEX_CHOICES
from journals import views as journals_views


urlpatterns = [
    # Journals
    url(r'^$', journals_views.journals, name='journals'),
    url(r'scipost_physics', RedirectView.as_view(url=reverse_lazy('scipost:landing_page',
                                                 args=['SciPostPhys']))),
    url(r'^journals_terms_and_conditions$',
        TemplateView.as_view(template_name='journals/journals_terms_and_conditions.html'),
        name='journals_terms_and_conditions'),
    url(r'^crossmark_policy$',
        TemplateView.as_view(template_name='journals/crossmark_policy.html'),
        name='crossmark_policy'),

    # Publication creation
    url(r'^admin/publications/{regex}/$'.format(regex=SUBMISSIONS_COMPLETE_REGEX),
        journals_views.DraftPublicationUpdateView.as_view(),
        name='update_publication'),
    url(r'^admin/publications/(?P<doi_label>{regex})/publish$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.PublicationPublishView.as_view(),
        name='publish_publication'),
    url(r'^admin/publications/(?P<doi_label>{regex})/approval$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.DraftPublicationApprovalView.as_view(),
        name='send_publication_for_approval'),
    url(r'^admin/publications/(?P<doi_label>{regex})/grants$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.PublicationGrantsView.as_view(),
        name='update_grants'),
    url(r'^admin/publications/(?P<doi_label>{regex})/grants/(?P<grant_id>[0-9]+)/remove$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.PublicationGrantsRemovalView.as_view(),
        name='remove_grant'),

    # Editorial and Administrative Workflow
    url(r'^admin/(?P<doi_label>{regex})/authors/add/(?P<contributor_id>[0-9]+)$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.add_author,
        name='add_author'),
    url(r'^admin/(?P<doi_label>{regex})/authors/add$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.add_author,
        name='add_author'),
    url(r'^admin/(?P<doi_label>{regex})/authors/mark_first/(?P<author_object_id>[0-9]+)$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.mark_first_author,
        name='mark_first_author'),
    url(r'^admin/(?P<doi_label>{regex})/manage_metadata$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.manage_metadata,
        name='manage_metadata'),
    url(r'^admin/(?P<issue_doi_label>[a-zA-Z]+.[0-9]+.[0-9]+)/manage_metadata$',
        journals_views.manage_metadata,
        name='manage_metadata'),
    url(r'^admin/(?P<journal_doi_label>{regex})/manage_metadata$'.format(regex=REGEX_CHOICES),
        journals_views.manage_metadata,
        name='manage_metadata'),
    url(r'^admin/manage_metadata/$',
        journals_views.manage_metadata,
        name='manage_metadata'),
    url(r'^admin/(?P<doi_label>{regex})/citation_list_metadata$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.CitationUpdateView.as_view(),
        name='create_citation_list_metadata'),
    url(r'^admin/(?P<doi_label>{regex})/update_references$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.update_references, name='update_references'),
    url(r'^admin/(?P<doi_label>{regex})/funders/create_metadata$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.FundingInfoView.as_view(),
        name='create_funding_info_metadata'),
    url(r'^admin/(?P<doi_label>{regex})/funders/add_generic$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.add_generic_funder,
        name='add_generic_funder'),
    url(r'^admin/(?P<doi_label>{regex})/grants/add$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.add_associated_grant,
        name='add_associated_grant'),

    # Metadata handling
    url(r'^admin/(?P<doi_label>{regex})/metadata/crossref/create$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.CreateMetadataXMLView.as_view(),
        name='create_metadata_xml'),
    url(r'^admin/(?P<doi_label>{regex})/metadata/crossref/deposit/(?P<option>[a-z]+)$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.metadata_xml_deposit,
        name='metadata_xml_deposit'),
    url(r'^admin/(?P<doi_label>{regex})/metadata/DOAJ$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.produce_metadata_DOAJ,
        name='produce_metadata_DOAJ'),
    url(r'^admin/(?P<doi_label>{regex})/metadata/DOAJ/deposit$'.format(
            regex=PUBLICATION_DOI_REGEX),
        journals_views.metadata_DOAJ_deposit,
        name='metadata_DOAJ_deposit'),
    url(r'^admin/metadata/crossref/(?P<deposit_id>[0-9]+)/mark/(?P<success>[0-1])$',
        journals_views.mark_deposit_success,
        name='mark_deposit_success'),
    url(r'^admin/metadata/DOAJ/(?P<deposit_id>[0-9]+)/mark/(?P<success>[0-1])$',
        journals_views.mark_doaj_deposit_success,
        name='mark_doaj_deposit_success'),
    url(r'^admin/metadata/generic/(?P<type_of_object>[a-z]+)/(?P<object_id>[0-9]+)/metadata$',
        journals_views.generic_metadata_xml_deposit,
        name='generic_metadata_xml_deposit'),
    url(r'^admin/metadata/generic/(?P<deposit_id>[0-9]+)/mark/(?P<success>[0-1])$',
        journals_views.mark_generic_deposit_success,
        name='mark_generic_deposit_success'),
    url(r'^admin/generic/(?P<type_of_object>[a-z]+)/(?P<object_id>[0-9]+)/email_made_citable$',
        journals_views.email_object_made_citable,
        name='email_object_made_citable'),

    # Citedby
    url(r'^admin/citedby/$',
        journals_views.harvest_citedby_list,
        name='harvest_citedby_list'),
    url(r'^admin/citedby/(?P<doi_label>{regex})/harvest$'.format(regex=PUBLICATION_DOI_REGEX),
        journals_views.harvest_citedby_links,
        name='harvest_citedby_links'),

    # Reports
    url(r'^reports/$',
        journals_views.manage_report_metadata,
        name='manage_report_metadata'),
    url(r'^reports/(?P<report_id>[0-9]+)/sign$',
        journals_views.sign_existing_report,
        name='sign_existing_report'),
    url(r'^reports/(?P<report_id>[0-9]+)/mark_doi_needed/(?P<needed>[0-1])$',
        journals_views.mark_report_doi_needed,
        name='mark_report_doi_needed'),

    # Comments
    url(r'^comments/$',
        journals_views.manage_comment_metadata,
        name='manage_comment_metadata'),
    url(r'^comments/(?P<comment_id>[0-9]+)/mark_doi_needed/(?P<needed>[0-1])$',
        journals_views.mark_comment_doi_needed,
        name='mark_comment_doi_needed'),
]
