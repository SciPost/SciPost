from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.NewsListView.as_view(), name='news'),
]
