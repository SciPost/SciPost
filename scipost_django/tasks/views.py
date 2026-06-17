__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from colleges.permissions import is_edadmin_or_active_fellow
from submissions.models.assignment import EditorialAssignment
from submissions.models.recommendation import EICRecommendation
from submissions.models.submission import Submission
from tasks.forms import TaskListSearchForm
from tasks.tasks.task_kinds import get_all_task_kinds


@login_required
@user_passes_test(is_edadmin_or_active_fellow)
def tasklist(request):
    """Displays list of tasks for Fellows."""
    assignments = EditorialAssignment.objects.filter(to=request.user.contributor)

    context = {
        "assignments_to_consider": assignments.invited().select_related("submission"),
        "assignments_ongoing": assignments.ongoing().select_related("submission"),
        "recs_to_vote_on": EICRecommendation.objects.user_must_vote_on(
            request.user
        ).select_related("submission"),
        "recs_current_voted": EICRecommendation.objects.user_current_voted(
            request.user
        ).select_related("submission"),
    }

    if fellowship := request.user.contributor.session_fellowship(request):
        context["submissions_to_appraise"] = (
            fellowship.pool.in_pool(fellowship.contributor.user)
            .filter(status=Submission.SEEKING_ASSIGNMENT)
            .annot_fully_appraised_by(fellowship.contributor)
            .filter(is_fully_appraised=False)
            .prefetch_related("specialties")
            .select_related("preprint", "acad_field")
        )

    return render(request, "tasks/tasklist.html", context)


@login_required
@user_passes_test(is_edadmin_or_active_fellow)
def tasklist_new_grouped(request):
    """Displays a grouped list of tasks"""

    context = {
        "kinds_with_tasks": {
            task_type: task_type.get_tasks()
            for task_type in get_all_task_kinds(request.user)
        }
    }
    return render(request, "tasks/tasklist_new_grouped.html", context)


@login_required
@user_passes_test(is_edadmin_or_active_fellow)
def tasklist_new(request):
    form = TaskListSearchForm(request.GET, user=request.user)

    tasks = []
    if form.is_valid():
        tasks = form.search()

    context = {
        "form": form,
        "tasks": tasks,
    }

    # If htmx request, return only the task list
    if request.headers.get("HX-Request") == "true":
        return render(request, "tasks/_hx_task_table.html", context)

    return render(request, "tasks/tasklist_new.html", context)
