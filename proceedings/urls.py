from django.conf.urls import url

from . import views

urlpatterns = [
    # Proceedings
    url(r'^proceedings/$', views.proceedings, name='proceedings'),
]
