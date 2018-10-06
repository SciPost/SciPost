__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.timesheets, name='finance'),

    url(
        r'^subsidies/$',
        views.SubsidyListView.as_view(),
        name='subsidies'
    ),
    url(
        r'^subsidies/add/$',
        views.SubsidyCreateView.as_view(),
        name='subsidy_create'
    ),
    url(
        r'^subsidies/(?P<pk>[0-9]+)/update/$',
        views.SubsidyUpdateView.as_view(),
        name='subsidy_update'
        ),
    url(
        r'^subsidies/(?P<pk>[0-9]+)/delete/$',
        views.SubsidyDeleteView.as_view(),
        name='subsidy_delete'
    ),


    url(r'^timesheets$', views.timesheets, name='timesheets'),
    url(r'^logs/(?P<slug>\d+)/delete$', views.LogDeleteView.as_view(), name='log_delete'),
]
