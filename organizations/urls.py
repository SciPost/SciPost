__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'organizations'

urlpatterns = [
    path(
        'organization-autocomplete',
        views.OrganizationAutocompleteView.as_view(),
        name='organization-autocomplete',
        ),
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
        r'^get_organization_detail$',
        views.get_organization_detail,
        name='get_organization_detail'
    ),
    url(
        r'^(?P<pk>[0-9]+)/orgevent/add/$',
        views.OrganizationEventCreateView.as_view(),
        name='organizationevent_create'
    ),
    url(
        r'^organizationevents/$',
        views.OrganizationEventListView.as_view(),
        name='organizationevent_list'
    ),
    url(
        r'^add_contactperson/(?P<organization_id>[0-9]+)/$',
        views.ContactPersonCreateView.as_view(),
        name='contactperson_create'
    ),
    url(
        r'^contactperson/add/$',
        views.ContactPersonCreateView.as_view(),
        name='contactperson_create'
    ),
    url(
        r'^contactperson/(?P<pk>[0-9]+)/update/$',
        views.ContactPersonUpdateView.as_view(),
        name='contactperson_update'
    ),
    url(
        r'^contactperson/(?P<pk>[0-9]+)/delete/$',
        views.ContactPersonDeleteView.as_view(),
        name='contactperson_delete'
    ),
    url(
        r'^contactpersons/$',
        views.ContactPersonListView.as_view(),
        name='contactperson_list'
    ),
    url(
        r'^contactperson/(?P<contactperson_id>[0-9]+)/email/(?P<mail>followup)$',
        views.email_contactperson,
        name='email_contactperson'
    ),
    url(
        r'^contactperson/(?P<contactperson_id>[0-9]+)/email/$',
        views.email_contactperson,
        name='email_contactperson'
    ),
    url(
        # For upgrading a ContactPerson to a Contact
        r'^add_contact/(?P<organization_id>[0-9]+)/(?P<contactperson_id>[0-9]+)/$',
        views.organization_add_contact,
        name='add_contact'
    ),
    url(
        r'^add_contact/(?P<organization_id>[0-9]+)/$',
        views.organization_add_contact,
        name='add_contact'
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
    url(r'^contact/(?P<pk>[0-9]+)/$',
        views.ContactDetailView.as_view(),
        name='contact_details'
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
        r'^contactrole/(?P<contactrole_id>[0-9]+)/email/(?P<mail>renewal)$',
        views.email_contactrole,
        name='email_contactrole'
    ),
    url(
        r'^contactrole/(?P<contactrole_id>[0-9]+)/email/$',
        views.email_contactrole,
        name='email_contactrole'
    ),
]
