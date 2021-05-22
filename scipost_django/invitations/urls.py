__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from . import views

app_name = 'invitations'

urlpatterns = [
    url(r'^$', views.RegistrationInvitationsView.as_view(), name='list'),
    url(r'^sent$', views.RegistrationInvitationsSentView.as_view(), name='list_sent'),
    url(r'^contributors$',
        views.RegistrationInvitationsDraftContributorView.as_view(), name='list_contributors'),
    url(r'^fellows$', views.RegistrationInvitationsFellowView.as_view(), name='list_fellows'),
    url(r'^new$', views.create_registration_invitation_or_citation, name='new'),
    url(r'^(?P<pk>[0-9]+)/$', views.RegistrationInvitationsUpdateView.as_view(), name='update'),
    url(r'^(?P<pk>[0-9]+)/add_citation$', views.RegistrationInvitationsAddCitationView.as_view(),
        name='add_citation'),
    url(r'^(?P<pk>[0-9]+)/delete$', views.RegistrationInvitationsDeleteView.as_view(),
        name='delete'),
    url(r'^(?P<pk>[0-9]+)/merge$', views.RegistrationInvitationsMergeView.as_view(),
        name='merge'),
    url(r'^(?P<pk>[0-9]+)/mark/(?P<label>sent)$', views.RegistrationInvitationsMarkView.as_view(),
        name='mark'),
    url(r'^(?P<pk>[0-9]+)/map_to_contributor/(?P<contributor_id>[0-9]+)/$',
        views.RegistrationInvitationsMapToContributorView.as_view(),
        name='map_to_contributor'),
    url(r'^(?P<pk>[0-9]+)/send_reminder$', views.RegistrationInvitationsReminderView.as_view(),
        name='send_reminder'),
    url(r'^cleanup$', views.cleanup, name='cleanup'),

    url(r'^citations$', views.CitationNotificationsView.as_view(),
        name='citation_notification_list'),
    url(r'^citations/(?P<pk>[0-9]+)$', views.CitationNotificationsProcessView.as_view(),
        name='citation_notification_process'),
]
