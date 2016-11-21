from django.conf.urls import include, url

from django.views.generic import TemplateView

#from . import views
from journals import views as journals_views

urlpatterns = [
    # Journals
    url(r'^$', journals_views.journals, name='journals'),
    url(r'^journals_terms_and_conditions$', 
        TemplateView.as_view(template_name='journals/journals_terms_and_conditions.html'), 
        name='journals_terms_and_conditions'),

    # SciPost Physics
    url(r'^scipost_physics$', 
        journals_views.scipost_physics, 
        name='scipost_physics'),
    url(r'^scipost_physics/issues$', 
        journals_views.scipost_physics_issues, 
        name='scipost_physics_issues'),
    url(r'^scipost_physics/recent$', 
        journals_views.scipost_physics_recent, 
        name='scipost_physics_recent'),
    url(r'^scipost_physics/accepted$', 
        journals_views.scipost_physics_accepted, 
        name='scipost_physics_accepted'),
    url(r'^scipost_physics/info_for_authors$', 
        journals_views.scipost_physics_info_for_authors, 
        name='scipost_physics_info_for_authors'),
    url(r'^scipost_physics/about$', 
        journals_views.scipost_physics_about, 
        name='scipost_physics_about'),

    url(r'^scipost_physics/(?P<volume_nr>[0-9]+)/(?P<issue_nr>[0-9]+)$',
        journals_views.scipost_physics_issue_detail,
        name='scipost_physics_issue_detail'),

    # Editorial and Administrative Workflow
    url(r'^initiate_publication$', 
        journals_views.initiate_publication, 
        name='initiate_publication'),
    url(r'^validate_publication$', 
        journals_views.validate_publication, 
        name='validate_publication'),
    #url(r'^create_citation_list_metadata/(?P<publication_id>[0-9]+)$',
    url(r'^create_citation_list_metadata/(?P<doi_string>10.21468/[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.create_citation_list_metadata,
        name='create_citation_list_metadata'),
    url(r'^create_funding_info_metadata/(?P<doi_string>10.21468/[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.create_funding_info_metadata,
        name='create_funding_info_metadata'),
    #url(r'^create_metadata_xml/(?P<publication_id>[0-9]+)$',
    url(r'^create_metadata_xml/(?P<doi_string>10.21468/[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
        journals_views.create_metadata_xml,
        name='create_metadata_xml'),
    # url(r'^test_metadata_xml_deposit/(?P<doi_string>10.21468/[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})$',
    #     journals_views.test_metadata_xml_deposit,
    #     name='test_metadata_xml_deposit'),
    url(r'^metadata_xml_deposit/(?P<doi_string>10.21468/[a-zA-Z]+.[0-9]+.[0-9]+.[0-9]{3,})/(?P<option>[a-z]+)$',
        journals_views.metadata_xml_deposit,
        name='metadata_xml_deposit'),
]
