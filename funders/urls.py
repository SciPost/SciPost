from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$', views.funders,
        name='funders'),
    url(r'^query_crossref_for_funder$',
        views.query_crossref_for_funder,
        name='query_crossref_for_funder'),
    url(r'^add_funder$',
        views.add_funder,
        name='add_funder'),
    url(r'^add_grant$',
        views.add_grant,
        name='add_grant'),
]
