__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
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
    url(
        r'^add_contact/(?P<organization_id>[0-9]+)/$',
        views.organization_add_contact,
        name='add_contact'
    ),
    url(
        r'^contactrole/(?P<pk>[0-9]+)/update/$',
        views.ContactRoleUpdateView.as_view(),
        name='contactrole_update'
    ),
    url(
        r'^contactrole/(?P<pk>[0-9]+)/delete/$',
        views.ContactRoleDeleteView.as_view(),
        name='contactrole_delete'
    ),
    url(
        r'^activate/(?P<activation_key>.+)$',
        views.activate_account,
        name='activate_account'
    ),
    url(
        r'^dashboard/$',
        views.dashboard,
        name='dashboard'
    ),
]
