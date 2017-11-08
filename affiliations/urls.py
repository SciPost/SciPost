from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.InstitutionListView.as_view(), name='institutions'),
    url(r'^(?P<institution_id>[0-9]+)/$', views.InstitutionUpdateView.as_view(),
        name='institution_details'),
    url(r'^(?P<institution_id>[0-9]+)/merge$', views.merge_institutions,
        name='merge_institutions'),
]
