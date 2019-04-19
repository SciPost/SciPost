__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url

from submissions.constants import SUBMISSIONS_COMPLETE_REGEX

from . import views

urlpatterns = [
    # Editorial Colleges: public view
    url(
        r'^$',
        views.EditorialCollegesView.as_view(),
        name='colleges'
    ),
    # Fellowships
    url(
        r'^fellowships/(?P<discipline>[a-zA-Z]+)/(?P<expertise>[a-zA-Z:]+)/$',
        views.FellowshipListView.as_view(),
        name='fellowships'
    ),
    url(
        r'^fellowships/(?P<discipline>[a-zA-Z]+)/$',
        views.FellowshipListView.as_view(),
        name='fellowships'
    ),
    url(
        r'^fellowships/$',
        views.FellowshipListView.as_view(),
        name='fellowships'
    ),
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

    # Potential Fellowships
    url(
        r'^potentialfellowships/add/$',
        views.PotentialFellowshipCreateView.as_view(),
        name='potential_fellowship_create'
    ),
    url(
        r'^potentialfellowships/(?P<pk>[0-9]+)/update/$',
        views.PotentialFellowshipUpdateView.as_view(),
        name='potential_fellowship_update'
    ),
    url(
        r'^potentialfellowsships/(?P<pk>[0-9]+)/update_status/$',
        views.PotentialFellowshipUpdateStatusView.as_view(),
        name='potential_fellowship_update_status'
    ),
    url(
        r'^potentialfellowships/(?P<pk>[0-9]+)/delete/$',
        views.PotentialFellowshipDeleteView.as_view(),
        name='potential_fellowship_delete'
    ),
    url(
        r'^potentialfellowships/(?P<pk>[0-9]+)/events/add/$',
        views.PotentialFellowshipEventCreateView.as_view(),
        name='potential_fellowship_event_create'
    ),
    url(
        r'^potentialfellowships/(?P<potfel_id>[0-9]+)/vote/(?P<vote>[AND])/$',
        views.vote_on_potential_fellowship,
        name='vote_on_potential_fellowship'
    ),
    url(
        r'^potentialfellowships/(?P<pk>[0-9]+)/email_initial/$',
        views.PotentialFellowshipInitialEmailView.as_view(),
        name='potential_fellowship_email_initial'
    ),
    url(
        r'^potentialfellowships/(?P<pk>[0-9]+)/$',
        views.PotentialFellowshipDetailView.as_view(),
        name='potential_fellowship_detail'
    ),
    url(
        r'^potentialfellowships/(?P<discipline>[a-zA-Z]+)/(?P<expertise>[a-zA-Z:]+)/$',
        views.PotentialFellowshipListView.as_view(),
        name='potential_fellowships'
    ),
    url(
        r'^potentialfellowships/(?P<discipline>[a-zA-Z]+)/$',
        views.PotentialFellowshipListView.as_view(),
        name='potential_fellowships'
    ),
    url(
        r'^potentialfellowships/$',
        views.PotentialFellowshipListView.as_view(),
        name='potential_fellowships'
    ),
]
