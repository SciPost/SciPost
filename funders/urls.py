__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'funders'

urlpatterns = [
    url(r'^$', views.funders, name='funders'),
    url(r'^dashboard$', views.funders_dashboard, name='funders_dashboard'),
    url(r'^query_crossref_for_funder$', views.query_crossref_for_funder,
        name='query_crossref_for_funder'),
    url(r'^add$', views.add_funder, name='add_funder'),
    url(r'^(?P<funder_id>[0-9]+)/$', views.funder_publications, name='funder_publications'),
    url(r'^grants/add$', views.CreateGrantView.as_view(), name='add_grant'),
    url(r'^(?P<pk>[0-9]+)/link_to_organization/$',
        views.LinkFunderToOrganizationView.as_view(),
        name='link_to_organization'),
]
