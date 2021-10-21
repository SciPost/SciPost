__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = 'mailing_lists'

urlpatterns = [
    # Mailchimp
    path(
        '',
        views.MailchimpListView.as_view(),
        name='overview'
    ),
    path(
        'sync',
        views.syncronize_lists,
        name='sync_lists'
    ),
    path(
        'sync/<str:list_id>/members',
        views.syncronize_members,
        name='sync_members'
    ),
    path(
        '<str:list_id>/',
        views.ListDetailView.as_view(),
        name='list_detail'
    ),
    path(
        'non_registered/export',
        views.export_non_registered_invitations,
        name='export_non_registered_invitations'
    ),
]
