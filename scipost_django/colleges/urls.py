__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django.urls import path

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
    path(
        'fellowship-autocomplete',
        views.FellowshipAutocompleteView.as_view(),
        name='fellowship-autocomplete'
    ),
    path(
        '_hx_fellowship_dynsel_list',
        views._hx_fellowship_dynsel_list,
        name='_hx_fellowship_dynsel_list'
    ),
    path(
        'fellowships/<int:contributor_id>/add/',
        views.FellowshipCreateView.as_view(),
        name='fellowship_create'),
    path(
        'fellowships/<int:pk>/update/',
        views.FellowshipUpdateView.as_view(),
        name='fellowship_update'),
    path(
        'fellowships/<int:pk>/',
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
    path(
        'fellowships/<int:pk>/email_start/',
        views.FellowshipStartEmailView.as_view(),
        name='fellowship_email_start'
    ),
    path(
        'fellowships/submissions/<identifier:identifier_w_vn_nr>/',
        views.submission_fellowships,
        name='submission'
    ),
    path(
        'fellowships/submissions/<identifier:identifier_w_vn_nr>/add',
        views.submission_add_fellowship,
        name='submission_add_fellowship'
    ),
    path(
        'fellowships/<int:id>/submissions/<identifier:identifier_w_vn_nr>/remove',
        views.fellowship_remove_submission,
        name='fellowship_remove_submission'
    ),
    path(
        'fellowships/<int:id>/submissions/add',
        views.fellowship_add_submission,
        name='fellowship_add_submission'
    ),
    path(
        'fellowships/<int:id>/proceedings/add',
        views.fellowship_add_proceedings,
        name='fellowship_add_proceedings'
    ),
    path(
        'fellowships/<int:id>/proceedings/<int:proceedings_id>/remove',
        views.fellowship_remove_proceedings,
        name='fellowship_remove_proceedings'
    ),

    # Potential Fellowships
    path(
        'potentialfellowships/add/',
        views.PotentialFellowshipCreateView.as_view(),
        name='potential_fellowship_create'
    ),
    path(
        'potentialfellowships/<int:pk>/update/',
        views.PotentialFellowshipUpdateView.as_view(),
        name='potential_fellowship_update'
    ),
    path(
        'potentialfellowsships/<int:pk>/update_status/',
        views.PotentialFellowshipUpdateStatusView.as_view(),
        name='potential_fellowship_update_status'
    ),
    path(
        'potentialfellowships/<int:pk>/delete/',
        views.PotentialFellowshipDeleteView.as_view(),
        name='potential_fellowship_delete'
    ),
    path(
        'potentialfellowships/<int:pk>/events/add/',
        views.PotentialFellowshipEventCreateView.as_view(),
        name='potential_fellowship_event_create'
    ),
    path(
        'potentialfellowships/<int:potfel_id>/vote/<str:vote>/',
        views.vote_on_potential_fellowship,
        name='vote_on_potential_fellowship'
    ),
    path(
        'potentialfellowships/<int:pk>/email_initial/',
        views.PotentialFellowshipInitialEmailView.as_view(),
        name='potential_fellowship_email_initial'
    ),
    path(
        'potentialfellowships/<int:pk>/',
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
