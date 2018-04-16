__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^statistics/(?P<journal_doi_label>[a-zA-Z]+)/(?P<volume_nr>[0-9]+)/(?P<issue_nr>[0-9]+)$',
        views.statistics, name='statistics'),
    url(r'^statistics/(?P<journal_doi_label>[a-zA-Z]+)/(?P<volume_nr>[0-9]+)$',
        views.statistics, name='statistics'),
    url(r'^statistics/(?P<journal_doi_label>[a-zA-Z]+)$', views.statistics, name='statistics'),
    url(r'^statistics/(?P<journal_doi_label>[a-zA-Z]+)/year/(?P<year>[0-9]{4,})$',
        views.statistics, name='statistics'),
    url(r'^statistics$', views.statistics, name='statistics'),
]
