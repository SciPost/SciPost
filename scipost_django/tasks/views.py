__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from datetime import datetime
from itertools import groupby

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import OuterRef, Subquery
from django.shortcuts import render

from colleges.permissions import is_edadmin_or_active_fellow
from submissions.models.assignment import EditorialAssignment
from submissions.models.recommendation import EICRecommendation
from submissions.models.submission import Submission
from tasks.forms import TaskListSearchForm
from tasks.tasks.task_kinds import get_all_task_kinds

from typing import Any

@login_required
@user_passes_test(is_edadmin_or_active_fellow)
def tasklist(request):
    """Displays list of tasks for Fellows."""
    assignments = EditorialAssignment.objects.filter(to=request.user.contributor)

    ongoing_submissions_by_thread = groupby(
        Submission.objects.filter(
            thread_hash__in=assignments.ongoing().values("submission__thread_hash")
        )
        .annotate(
            editorial_assignment_date=Subquery(
                assignments.filter(submission=OuterRef("pk")).values("date_created")[:1]
            )
        )
        .select_related("preprint")
        .prefetch_related("editorial_assignments")
        .order_by("thread_hash", "-id"),
        key=lambda sub: sub.thread_hash,
    )

    ongoing_submission_threads: list[dict[str, Any]] = []
    for thread_hash, submissions in ongoing_submissions_by_thread:
        submissions = list(submissions)

        submission_dicts: list[dict[str, Any]] = [
            {
                "submission": sub,
                "version": len(submissions) - i + 1,
                "cycle_actions": list(sub.cycle.required_actions),
            }
            for i, sub in enumerate(submissions, start=1)
        ]

        latest_assignment: datetime = max(
            [
                assignment_date or datetime.min
                for sub in submissions
                if (assignment_date := getattr(sub, "editorial_assignment_date", None))
                is not None
            ],
        )

        total_actions = sum(
            len(sub_dict["cycle_actions"]) for sub_dict in submission_dicts
        )
        ongoing_submission_threads.append(
            {
                "thread_hash": thread_hash,
                "submissions": submission_dicts,
                "total_actions": total_actions,
                "has_actions": total_actions > 0,
                "latest_assignment_date": latest_assignment,
            }
        )

    ongoing_submission_threads.sort(key=lambda dict_info: dict_info["has_actions"])

    context = {
        "assignments_to_consider": assignments.invited().select_related("submission"),
        "ongoing_submission_threads": ongoing_submission_threads,
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
