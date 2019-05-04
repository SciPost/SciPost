__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'mailing_lists'

urlpatterns = [
    # Mailchimp
    url(r'^$', views.MailchimpListView.as_view(), name='overview'),
    url(r'^sync$', views.syncronize_lists, name='sync_lists'),
    url(r'^sync/(?P<list_id>[0-9a-zA-Z]+)/members$', views.syncronize_members, name='sync_members'),
    url(r'^(?P<list_id>[0-9a-zA-Z]+)/$', views.ListDetailView.as_view(), name='list_detail'),
    url(r'^non_registered/export$', views.export_non_registered_invitations,
        name='export_non_registered_invitations'),
]
