from django.conf.urls import url
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from journals import views as journals_views

urlpatterns = [
    # Journals
    url(r'^$', TemplateView.as_view(template_name='journals/journals.html'), name='journals'),
    url(r'scipost_physics', RedirectView.as_view(url=reverse_lazy('scipost:landing_page', args=['SciPostPhys']))),
    url(r'^journals_terms_and_conditions$',
        TemplateView.as_view(template_name='journals/journals_terms_and_conditions.html'),
        name='journals_terms_and_conditions'),

    # Editorial and Administrative Workflow
    url(r'^initiate_publication$',
        journals_views.initiate_publication,
        name='initiate_publication'),
    url(r'^validate_publication$',
        journals_views.validate_publication,
        name='validate_publication'),
    url(r'^mark_first_author/(?P<publication_id>[0-9]+)/(?P<contributor_id>[0-9]+)$',
        journals_views.mark_first_author,
        name='mark_first_author'),
    url(r'^mark_first_author_unregistered/(?P<publication_id>[0-9]+)/(?P<unregistered_author_id>[0-9]+)$',
        journals_views.mark_first_author_unregistered,
        name='mark_first_author_unregistered'),
    url(r'^add_author/(?P<publication_id>[0-9]+)/(?P<contributor_id>[0-9]+)$',
        journals_views.add_author,
        name='add_author'),
    url(r'^add_author/(?P<publication_id>[0-9]+)$',
        journals_views.add_author,
        name='add_author'),
    url(r'^add_unregistered_author/(?P<publication_id>[0-9]+)/(?P<unregistered_author_id>[0-9]+)$',
        journals_views.add_unregistered_author,
        name='add_unregistered_author'),
    url(r'^add_new_unreg_author/(?P<publication_id>[0-9]+)$',
        journals_views.add_new_unreg_author,
        name='add_new_unreg_author'),
    url(r'^create_citation_list_metadata/(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.create_citation_list_metadata,
        name='create_citation_list_metadata'),
    url(r'^create_funding_info_metadata/(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.create_funding_info_metadata,
        name='create_funding_info_metadata'),
    url(r'^create_metadata_xml/(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.create_metadata_xml,
        name='create_metadata_xml'),
    url(r'^metadata_xml_deposit/(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})/(?P<option>[a-z]+)$',
        journals_views.metadata_xml_deposit,
        name='metadata_xml_deposit'),
    url(r'^harvest_citedby_links/$',
        journals_views.harvest_all_publications,
        name='harvest_all_publications'),
    url(r'^harvest_citedby_links/(?P<doi_label>[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.harvest_citedby_links,
        name='harvest_citedby_links'),
]
