__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.conf.urls import url
from django.urls import path

from submissions.constants import SUBMISSIONS_COMPLETE_REGEX

from . import views


app_name = 'colleges'

urlpatterns = [
    # Editorial Colleges: public view
    path(
        '',
        views.CollegeListView.as_view(),
        name='colleges'
    ),
    path(
        '<college:college>',
        views.CollegeDetailView.as_view(),
        name='college_detail'
    ),
    path(
        '<college:college>/email_Fellows',
        views.email_College_Fellows,
        name='email_College_Fellows'
    ),

    # Fellowships
    url(
        r'^fellowships/(?P<contributor_id>[0-9]+)/add/$',
        views.FellowshipCreateView.as_view(),
        name='fellowship_create'),
    url(
        r'^fellowships/(?P<pk>[0-9]+)/update/$',
        views.FellowshipUpdateView.as_view(),
        name='fellowship_update'),
    url(
        r'^fellowships/(?P<pk>[0-9]+)/$',
        views.FellowshipDetailView.as_view(),
        name='fellowship_detail'
    ),
    path(
        'fellowships/<acad_field:acad_field>/<specialty:specialty>',
        views.FellowshipListView.as_view(),
        name='fellowships'
    ),
    path(
        'fellowships/<acad_field:acad_field>',
        views.FellowshipListView.as_view(),
        name='fellowships'
    ),
    path(
        'fellowships',
        views.FellowshipListView.as_view(),
        name='fellowships'
    ),

    url(
        r'^fellowships/(?P<pk>[0-9]+)/email_start/$',
        views.FellowshipStartEmailView.as_view(),
        name='fellowship_email_start'
    ),

    url(r'^fellowships/submissions/{regex}/$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_fellowships,
        name='submission'),
    url(r'^fellowships/submissions/{regex}/add$'.format(
        regex=SUBMISSIONS_COMPLETE_REGEX), views.submission_add_fellowship,
        name='submission_add_fellowship'),

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
    path(
        'potentialfellowships/<acad_field:acad_field>/<specialty:specialty>',
        views.PotentialFellowshipListView.as_view(),
        name='potential_fellowships'
    ),
    path(
        'potentialfellowships/<acad_field:acad_field>',
        views.PotentialFellowshipListView.as_view(),
        name='potential_fellowships'
    ),
    path(
        'potentialfellowships',
        views.PotentialFellowshipListView.as_view(),
        name='potential_fellowships'
    ),
]
