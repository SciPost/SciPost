__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.OrganizationListView.as_view(),
        name='organizations'
    ),
    url(
        r'^add/$',
        views.OrganizationCreateView.as_view(),
        name='organization_create'
    ),
    url(
        r'^(?P<pk>[0-9]+)/update/$',
        views.OrganizationUpdateView.as_view(),
        name='organization_update'
    ),
    url(
        r'^(?P<pk>[0-9]+)/delete/$',
        views.OrganizationDeleteView.as_view(),
        name='organization_delete'
    ),
    url(
        r'^(?P<pk>[0-9]+)/$',
        views.OrganizationDetailView.as_view(),
        name='organization_details'
    ),
]
