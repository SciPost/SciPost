from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.funders, name='funders'),
    url(r'^query_crossref_for_funder$', views.query_crossref_for_funder,
        name='query_crossref_for_funder'),
    url(r'^funders/add$', views.add_funder, name='add_funder'),
    url(r'^funders/(?P<funder_id>[0-9]+)/$', views.funder_publications,
        name='funder_publications'),
    url(r'^grants/add$', views.add_grant, name='add_grant'),
]
