from django.conf.urls import url

from . import views

urlpatterns = [
    # Commentaries
    url(r'^fellowships/$', views.fellowships, name='fellowships'),
    url(r'^fellowships/(?P<id>[0-9]+)$', views.fellowship_detail, name='fellowship'),
]
