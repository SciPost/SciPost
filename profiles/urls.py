__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'profiles'

urlpatterns = [
    path(
        'profile-autocomplete',
        views.ProfileAutocompleteView.as_view(),
        name='profile-autocomplete'
    ),
    url(
        r"^add/(?P<from_type>[a-z]+)/(?P<pk>[0-9]+)$",
        views.ProfileCreateView.as_view(),
        name='profile_create'
    ),
    url(
        r"^add/$",
        views.ProfileCreateView.as_view(),
        name='profile_create'
    ),
    url(
        r'^match/(?P<profile_id>[0-9]+)/(?P<from_type>[a-z]+)/(?P<pk>[0-9]+)$',
        views.profile_match,
        name='profile_match'
    ),
    url(
        r'^(?P<pk>[0-9]+)/update/$',
        views.ProfileUpdateView.as_view(),
        name='profile_update'
    ),
    url(
        r'^(?P<pk>[0-9]+)/delete/$',
        views.ProfileDeleteView.as_view(),
        name='profile_delete'
    ),
    url(
        r'^$',
        views.ProfileListView.as_view(),
        name='profiles'
    ),
    url(
        r'^(?P<pk>[0-9]+)/$',
        views.ProfileDetailView.as_view(),
        name='profile_detail'
    ),
    url(
        r'^merge/$',
        views.profile_merge,
        name='merge'
    ),
    url(
        r'^duplicates/$',
        views.ProfileDuplicateListView.as_view(),
        name='duplicates'
    ),
    url(
        r'^(?P<profile_id>[0-9]+)/add_email$',
        views.add_profile_email,
        name='add_profile_email'
    ),
    url(
        r'^emails/(?P<email_id>[0-9]+)/make_primary$',
        views.email_make_primary,
        name='email_make_primary'
    ),
    url(
        r'^emails/(?P<email_id>[0-9]+)/toggle$',
        views.toggle_email_status,
        name='toggle_email_status'
    ),
    url(
        r'^emails/(?P<email_id>[0-9]+)/delete$',
        views.delete_profile_email,
        name='delete_profile_email'
    ),
    url(
        r'^(?P<profile_id>[0-9]+)/affiliation/add/$',
        views.AffiliationCreateView.as_view(),
        name='affiliation_create'
    ),
    url(
        r'^(?P<profile_id>[0-9]+)/affiliation/(?P<pk>[0-9]+)/update/$',
        views.AffiliationUpdateView.as_view(),
        name='affiliation_update'
    ),
    url(
        r'^(?P<profile_id>[0-9]+)/affiliation/(?P<pk>[0-9]+)/delete/$',
        views.AffiliationDeleteView.as_view(),
        name='affiliation_delete'
    ),
]
