__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Max, OuterRef, Prefetch, Subquery
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, render

from edadmin.forms.monitor import EdAdminFellowshipSearchForm


from colleges.models import College, Fellowship
from colleges.permissions import is_edadmin_or_senior_fellow
from scipost.models import UnavailabilityPeriod
from submissions.models.qualification import Qualification
from submissions.models.submission import Submission


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def fellow_activity(request):
    """
    Monitor activity of Fellows for the Colleges to which this user belongs.
    """
    if request.user.contributor.is_ed_admin:
        colleges = College.objects.all()
    else:
        colleges = College.objects.filter(
            pk__in=[f.college.id for f in request.user.contributor.fellowships.all()]
        )
    context = {
        "colleges": colleges,
    }
    return render(
        request,
        "edadmin/monitor/fellow_activity.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_college_fellow_activity_table(request, college):
    form = EdAdminFellowshipSearchForm(request.POST or None, college=college)
    form.is_valid()
    fellowships = form.search()

    current_unavailability_periods = UnavailabilityPeriod.objects.today()
    prefetch_current_unavailability_periods = Prefetch(
        "contributor__unavailability_periods",
        queryset=current_unavailability_periods,
        to_attr="current_unavailability_periods",
    )
    prefetch_EIC_in_stage_in_refereeing = Prefetch(
        "contributor__EIC",
        queryset=Submission.objects.in_stage_in_refereeing(),
        to_attr="EIC_in_stage_in_refereeing",
    )

    in_pool_seeking_assignment = Submission.objects.filter(
        status=Submission.SEEKING_ASSIGNMENT,
        fellows__id__exact=OuterRef("id"),
    )
    qualifications_by_fellow = Qualification.objects.filter(
        fellow=OuterRef("contributor_id"),
        submission__status=Submission.SEEKING_ASSIGNMENT,
    )

    fellowships = fellowships.prefetch_related(
        "contributor__dbuser",
        "contributor__profile__specialties",
        prefetch_current_unavailability_periods,
        prefetch_EIC_in_stage_in_refereeing,
    ).annotate(
        nr_visible=Coalesce(
            Subquery(
                in_pool_seeking_assignment.values("fellows")
                .annotate(nr=(Count("fellows")))
                .values("nr")
            ),
            0,
        ),
        nr_appraised=Coalesce(
            Subquery(
                qualifications_by_fellow.values("fellow")
                .annotate(nr=(Count("fellow")))
                .values("nr")
            ),
            0,
        ),
        latest_appraisal_datetime=Subquery(
            qualifications_by_fellow.values("fellow")
            .annotate(latest=Max("datetime"))
            .values("latest")
        ),
    )
    context = {
        "college": college,
        "fellowships": fellowships,
        "form": form,
    }
    return render(
        request,
        "edadmin/monitor/_hx_college_fellow_activity_table.html",
        context,
    )


@login_required
@user_passes_test(is_edadmin_or_senior_fellow)
def _hx_fellow_stage_assignment_appraisals_table(request, fellowship_id: int):
    """
    Provide a table of this Fellow's appraisals for Submissions in Assignment stage.
    """
    fellowship = get_object_or_404(Fellowship, pk=fellowship_id)
    context = {
        "fellowship": fellowship,
        "submissions_in_assignment": Submission.objects.all()
        .annot_authors_have_nonexpired_coi_with_profile(fellowship.contributor.profile)
        .in_stage_assignment(),
    }
    return render(
        request,
        "edadmin/monitor/_hx_fellow_stage_assignment_appraisals_table.html",
        context,
    )
