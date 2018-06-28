__copyright__ = "Copyright 2016-2018, Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from submissions.constants import SUBMISSIONS_COMPLETE_REGEX

from . import views

urlpatterns = [
    # Fellowships
    url(r'^fellowships/$', views.fellowships, name='fellowships'),
    url(r'^fellowships/add$', views.fellowship_add, name='fellowship_add'),
    url(r'^fellowships/(?P<id>[0-9]+)/$', views.fellowship_detail, name='fellowship'),
    url(r'^fellowships/(?P<id>[0-9]+)/edit$', views.fellowship_edit, name='fellowship_edit'),
    url(r'^fellowships/(?P<id>[0-9]+)/terminate$', views.fellowship_terminate,
        name='fellowship_terminate'),
    url(r'^fellowships/submissions/{regex}/$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_pool,
        name='submission'),
    url(r'^fellowships/submissions/{regex}/voting$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_voting_fellows,
        name='submission_voting_fellows'),
    url(r'^fellowships/submissions/{regex}/add$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_add_fellowship,
        name='submission_add_fellowship'),
    url(r'^fellowships/submissions/{regex}/voting/add$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_add_fellowship_voting,
        name='submission_add_fellowship_voting'),
    url(r'^fellowships/(?P<id>[0-9]+)/submissions/{regex}/remove$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.fellowship_remove_submission_voting,
        name='fellowship_remove_submission_voting'),

    url(r'^fellowships/(?P<id>[0-9]+)/submissions/{regex}/remove$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.fellowship_remove_submission,
        name='fellowship_remove_submission'),
    url(r'^fellowships/(?P<id>[0-9]+)/submissions/add$',
        views.fellowship_add_submission, name='fellowship_add_submission'),

    url(r'^fellowships/(?P<id>[0-9]+)/proceedings/add$',
        views.fellowship_add_proceedings, name='fellowship_add_proceedings'),
    url(r'^fellowships/(?P<id>[0-9]+)/proceedings/(?P<proceedings_id>[0-9]+)/remove$',
        views.fellowship_remove_proceedings, name='fellowship_remove_proceedings'),

    # Prospective Fellows
    url(r'^prospectivefellows/$',
        views.ProspectiveFellowListView.as_view(), name='prospective_Fellows'),
    url(r'^prospectivefellows/add/$',
        views.ProspectiveFellowCreateView.as_view(), name='prospective_Fellow_create'),
    url(r'^prospectivefellows/(?P<pk>[0-9]+)/update/$',
        views.ProspectiveFellowUpdateView.as_view(), name='prospective_Fellow_update'),
    url(r'^prospectivefellows/(?P<pk>[0-9]+)/delete/$',
        views.ProspectiveFellowDeleteView.as_view(), name='prospective_Fellow_delete'),
    url(r'^prospectivefellows/(?P<pk>[0-9]+)/events/add$',
        views.ProspectiveFellowEventCreateView.as_view(), name='prospective_Fellow_event_create'),
]
