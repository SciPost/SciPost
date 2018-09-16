__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^add/$',
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
        r'^(?P<discipline>[a-zA-Z]+)/(?P<expertise>[a-zA-Z:]+)/$',
        views.ProfileListView.as_view(),
        name='profiles'
        ),
    url(
        r'^(?P<discipline>[a-zA-Z]+)/$',
        views.ProfileListView.as_view(),
        name='profiles'
        ),
    url(
        r'^$',
        views.ProfileListView.as_view(),
        name='profiles'
    ),
]
