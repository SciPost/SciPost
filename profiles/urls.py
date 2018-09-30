__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
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
        r'^(?P<profile_id>[0-9]+)/add_alternative_email/$',
        views.add_alternative_email,
        name='add_alternative_email'
    ),
]
