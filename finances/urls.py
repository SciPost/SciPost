__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='finances/finances.html'), name='finances'),

    # Subsidies
    url(r'^subsidies/$', views.SubsidyListView.as_view(), name='subsidies'),
    url(r'^subsidies/add/$', views.SubsidyCreateView.as_view(), name='subsidy_create'),
    url(r'^subsidies/(?P<pk>[0-9]+)/update/$', views.SubsidyUpdateView.as_view(),
        name='subsidy_update'),
    url(r'^subsidies/(?P<pk>[0-9]+)/delete/$', views.SubsidyDeleteView.as_view(),
        name='subsidy_delete'),
    url(r'^subsidies/(?P<pk>[0-9]+)/$', views.SubsidyDetailView.as_view(), name='subsidy_details'),

    # Timesheets
    url(r'^timesheets$', views.timesheets, name='timesheets'),
    url(r'^timesheets/detailed$', views.timesheets_detailed, name='timesheets_detailed'),
    url(r'^logs/(?P<slug>\d+)/delete$', views.LogDeleteView.as_view(), name='log_delete'),
]
