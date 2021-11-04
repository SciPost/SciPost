__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import include, path, re_path
from django.views.generic import TemplateView

from . import views

app_name = 'theses'

urlpatterns = [
    # Thesis Links
    path(
        '',
        views.ThesisListView.as_view(),
        name='theses'
    ),
    re_path(
        r'^browse/(?P<nrweeksback>[0-9]{1,3})/$',
        views.ThesisListView.as_view(),
        name='browse'
    ),
    path(
        '<int:thesislink_id>/',
        views.thesis_detail,
        name='thesis'
    ),
    path(
        'request_thesislink',
        views.RequestThesisLink.as_view(),
        name='request_thesislink'
    ),
    path(
        'unvetted_thesislinks',
        views.UnvettedThesisLinks.as_view(),
        name='unvetted_thesislinks'
    ),
    path(
        'vet_thesislink/<int:pk>/',
        views.VetThesisLink.as_view(),
        name='vet_thesislink'
    ),
]
