from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.timesheets, name='finance'),
    url(r'^timesheets$', views.timesheets, name='timesheets'),
]
