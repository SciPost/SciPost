from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.timesheets, name='finance'),
    url(r'^timesheets$', views.timesheets, name='timesheets'),
    url(r'^logs/(?P<slug>\d+)/delete$', views.LogDeleteView.as_view(), name='log_delete'),
]
