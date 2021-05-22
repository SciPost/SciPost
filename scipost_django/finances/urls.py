__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.views.generic import TemplateView

from . import views

app_name = 'finances'

urlpatterns = [
    url(
        r'^$',
        views.finances,
        name='finances'
    ),
    url(
        r'^business_model/$',
        TemplateView.as_view(template_name='finances/business_model.html'),
        name='business_model'
    ),
    url(
        r'^apex$',
        views.apex,
        name='apex'
    ),

    # Subsidies
    url(r'^subsidies/$', views.SubsidyListView.as_view(), name='subsidies'),
    url(r'^subsidies/add/$', views.SubsidyCreateView.as_view(), name='subsidy_create'),
    url(r'^subsidies/(?P<pk>[0-9]+)/update/$', views.SubsidyUpdateView.as_view(),
        name='subsidy_update'),
    url(r'^subsidies/(?P<pk>[0-9]+)/delete/$', views.SubsidyDeleteView.as_view(),
        name='subsidy_delete'),
    url(r'^subsidies/(?P<pk>[0-9]+)/$', views.SubsidyDetailView.as_view(), name='subsidy_details'),
    url(r'^subsidies/(?P<subsidy_id>[0-9]+)/toggle_amount_visibility/$',
        views.subsidy_toggle_amount_public_visibility,
        name='subsidy_toggle_amount_public_visibility'),
    url(r'^subsidies/(?P<subsidy_id>[0-9]+)/attachments/add/$',
        views.SubsidyAttachmentCreateView.as_view(),
        name='subsidyattachment_create'),
    url(r'^subsidies/attachments/(?P<pk>[0-9]+)/update/$',
        views.SubsidyAttachmentUpdateView.as_view(),
        name='subsidyattachment_update'),
    url(r'^subsidies/attachments/(?P<pk>[0-9]+)/delete/$',
        views.SubsidyAttachmentDeleteView.as_view(),
        name='subsidyattachment_delete'),
    url(r'^subsidies/attachments/(?P<attachment_id>[0-9]+)/toggle_visibility/$',
        views.subsidy_attachment_toggle_public_visibility,
        name='subsidy_attachment_toggle_public_visibility'),
    url(r'^subsidies/(?P<subsidy_id>[0-9]+)/attachments/(?P<attachment_id>[0-9]+)$',
        views.subsidy_attachment, name='subsidy_attachment'),

    # Timesheets
    url(r'^timesheets$', views.timesheets, name='timesheets'),
    url(r'^timesheets/detailed$', views.timesheets_detailed, name='timesheets_detailed'),
    url(r'^logs/(?P<slug>\d+)/delete$', views.LogDeleteView.as_view(), name='log_delete'),
]
