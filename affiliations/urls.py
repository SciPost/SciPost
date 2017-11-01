from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.AffiliationListView.as_view(), name='affiliations'),
    url(r'^(?P<affiliation_id>[0-9]+)/$', views.AffiliationUpdateView.as_view(),
        name='affiliation_details'),
    url(r'^(?P<affiliation_id>[0-9]+)/merge$', views.merge_affiliations,
        name='merge_affiliations'),
]
