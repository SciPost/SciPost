__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import importlib
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from colleges.permissions import is_edadmin_or_active_fellow
from submissions.models.assignment import EditorialAssignment
from submissions.models.recommendation import EICRecommendation
from tasks.tasks.task import TaskKind


@login_required
@user_passes_test(is_edadmin_or_active_fellow)
def tasklist(request):
    """Displays list of tasks for Fellows."""
    context = {
        "assignments_to_consider": EditorialAssignment.objects.invited().filter(
            to=request.user.contributor
        ),
        "assignments_ongoing": request.user.contributor.editorial_assignments.ongoing(),
        "recs_to_vote_on": EICRecommendation.objects.user_must_vote_on(request.user),
        "recs_current_voted": EICRecommendation.objects.user_current_voted(
            request.user
        ),
    }
    return render(request, "tasks/tasklist.html", context)


@login_required
@user_passes_test(is_edadmin_or_active_fellow)
def tasklist_new(request):
    """Displays a grouped list of tasks"""
    # `task_types` should be the * import of task_kinds.py
    task_types = importlib.import_module("tasks.tasks.task_kinds").__all__
    context = {
        "kinds_with_tasks": {
            task_type: task_type.get_tasks()
            for task_type in task_types
            if issubclass(task_type, TaskKind)
            and task_type.is_user_eligible(request.user)
        }
    }
    return render(request, "tasks/tasklist_new.html", context)
