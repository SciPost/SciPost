__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from production import views as production_views

app_name = 'production'

urlpatterns = [
    url(r'^$', production_views.production, name='production'),
    url(r'^(?P<stream_id>[0-9]+)$', production_views.production, name='production'),
    url(r'^completed$', production_views.completed, name='completed'),
    url(r'^officers/new$', production_views.user_to_officer, name='user_to_officer'),
    url(r'^officers/(?P<officer_id>[0-9]+)/delete$', production_views.delete_officer,
        name='delete_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)$',
        production_views.stream, name='stream'),
    url(r'^streams/(?P<stream_id>[0-9]+)/status$',
        production_views.update_status, name='update_status'),
    url(r'^streams/(?P<stream_id>[0-9]+)/proofs/upload$',
        production_views.upload_proofs, name='upload_proofs'),
    url(r'^streams/(?P<stream_id>[0-9]+)/proofs/(?P<version>[0-9]+)$',
        production_views.proofs, name='proofs'),
    url(r'^streams/(?P<stream_id>[0-9]+)/proofs/(?P<version>[0-9]+)/decision/(?P<decision>accept|decline)$',
        production_views.decision, name='decision'),
    url(r'^streams/(?P<stream_id>[0-9]+)/proofs/(?P<version>[0-9]+)/send_to_authors$',
        production_views.send_proofs, name='send_proofs'),
    url(r'^streams/(?P<stream_id>[0-9]+)/proofs/(?P<version>[0-9]+)/toggle_access$',
        production_views.toggle_accessibility, name='toggle_accessibility'),
    url(r'^streams/(?P<stream_id>[0-9]+)/proofs/(?P<attachment_id>[0-9]+)/reply/pdf$',
        production_views.production_event_attachment_pdf, name='production_event_attachment_pdf'),
    url(r'^streams/(?P<stream_id>[0-9]+)/events/add$',
        production_views.add_event, name='add_event'),
    url(r'^streams/(?P<stream_id>[0-9]+)/logs/add$',
        production_views.add_work_log, name='add_work_log'),
    url(r'^streams/(?P<stream_id>[0-9]+)/officer/add$',
        production_views.add_officer, name='add_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)/officer/(?P<officer_id>[0-9]+)/remove$',
        production_views.remove_officer, name='remove_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)/invitations_officer/add$',
        production_views.add_invitations_officer, name='add_invitations_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)/invitations_officer/(?P<officer_id>[0-9]+)/remove$',
        production_views.remove_invitations_officer, name='remove_invitations_officer'),
    url(r'^streams/(?P<stream_id>[0-9]+)/supervisor/add$',
        production_views.add_supervisor, name='add_supervisor'),
    url(r'^streams/(?P<stream_id>[0-9]+)/supervisor/(?P<officer_id>[0-9]+)/remove$',
        production_views.remove_supervisor, name='remove_supervisor'),
    url(r'^streams/(?P<stream_id>[0-9]+)/mark_completed$',
        production_views.mark_as_completed, name='mark_as_completed'),
    url(r'^events/(?P<event_id>[0-9]+)/edit',
        production_views.UpdateEventView.as_view(), name='update_event'),
    url(r'^events/(?P<event_id>[0-9]+)/delete',
        production_views.DeleteEventView.as_view(), name='delete_event'),
    url(r'^proofs/(?P<slug>[0-9]+)$',
        production_views.proofs_pdf, name='proofs_pdf'),
    url(r'^proofs/(?P<slug>[0-9]+)/decision$',
        production_views.author_decision, name='author_decision'),
]
