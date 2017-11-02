from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.InstituteListView.as_view(), name='institutes'),
    url(r'^(?P<institute_id>[0-9]+)/$', views.InstituteUpdateView.as_view(),
        name='institute_details'),
    url(r'^(?P<institute_id>[0-9]+)/merge$', views.merge_institutes,
        name='merge_institutes'),
]
