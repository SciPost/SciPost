__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import include, url
from django.views.generic import TemplateView

from . import views

app_name = 'theses'

urlpatterns = [
    # Thesis Links
    url(r'^$', views.ThesisListView.as_view(), name='theses'),
    url(r'^browse/(?P<nrweeksback>[0-9]{1,3})/$', views.ThesisListView.as_view(), name='browse'),
    url(r'^(?P<thesislink_id>[0-9]+)/$', views.thesis_detail, name='thesis'),
    url(r'^request_thesislink$', views.RequestThesisLink.as_view(), name='request_thesislink'),
    url(r'^unvetted_thesislinks$', views.UnvettedThesisLinks.as_view(), name='unvetted_thesislinks'),
    url(r'^vet_thesislink/(?P<pk>[0-9]+)/$', views.VetThesisLink.as_view(), name='vet_thesislink'),
]
