from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # Citables
    url(r'^$', views.CitableListView.as_view(), name='citable-list'),
]
