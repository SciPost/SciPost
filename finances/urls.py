__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.timesheets, name='finance'),
    url(r'^timesheets$', views.timesheets, name='timesheets'),
    url(r'^logs/(?P<slug>\d+)/delete$', views.LogDeleteView.as_view(), name='log_delete'),
]
