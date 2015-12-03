from django.conf.urls import include, url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # Info
    url(r'^about$', views.about, name='about'),
    url(r'^description$', views.description, name='description'),
    url(r'^peer_witnessed_refereeing$', views.peer_witnessed_refereeing, name='peer_witnessed_refereeing'),
]
