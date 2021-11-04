__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

from . import views

app_name = 'invitations'

urlpatterns = [
    path(
        '',
        views.RegistrationInvitationsView.as_view(),
        name='list'
    ),
    path(
        'sent',
        views.RegistrationInvitationsSentView.as_view(),
        name='list_sent'
    ),
    path(
        'contributors',
        views.RegistrationInvitationsDraftContributorView.as_view(),
        name='list_contributors'
    ),
    path(
        'fellows',
        views.RegistrationInvitationsFellowView.as_view(),
        name='list_fellows'
    ),
    path(
        'new',
        views.create_registration_invitation_or_citation,
        name='new'
    ),
    path(
        '<int:pk>/',
        views.RegistrationInvitationsUpdateView.as_view(),
        name='update'
    ),
    path(
        '<int:pk>/add_citation',
        views.RegistrationInvitationsAddCitationView.as_view(),
        name='add_citation'
    ),
    path(
        '<int:pk>/delete',
        views.RegistrationInvitationsDeleteView.as_view(),
        name='delete'
    ),
    path(
        '<int:pk>/merge',
        views.RegistrationInvitationsMergeView.as_view(),
        name='merge'
    ),
    path(
        '<int:pk>/mark/<str:label>',
        views.RegistrationInvitationsMarkView.as_view(),
        name='mark'
    ),
    path(
        '<int:pk>/map_to_contributor/<int:contributor_id>/',
        views.RegistrationInvitationsMapToContributorView.as_view(),
        name='map_to_contributor'
    ),
    path(
        '<int:pk>/send_reminder',
        views.RegistrationInvitationsReminderView.as_view(),
        name='send_reminder'
    ),
    path(
        'cleanup',
        views.cleanup,
        name='cleanup'
    ),
    path(
        'citations',
        views.CitationNotificationsView.as_view(),
        name='citation_notification_list'
    ),
    path(
        'citations/<int:pk>',
        views.CitationNotificationsProcessView.as_view(),
        name='citation_notification_process'
    ),
]
