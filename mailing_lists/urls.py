from django.conf.urls import url

from . import views

urlpatterns = [
    # Mailchimp
    url(r'^$', views.MailchimpListView.as_view(), name='overview'),
    url(r'^sync/$', views.syncronize_lists, name='sync_lists'),
    url(r'^(?P<list_id>[0-9a-zA-Z]+)/$', views.ListDetailView.as_view(), name='list_detail'),
]
