__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from django import template
from django.db.models import Q, Avg, Count, Exists, OuterRef, Prefetch, Subquery, Value
from django.db.models.functions import Concat
from django.utils import timezone

from ethics.models import ConflictOfInterest, SubmissionClearance
from ontology.models.topic import TopicInterest
from scipost.models import UnavailabilityPeriod
from submissions.constants import EVENT_FOR_EDADMIN
from submissions.models.submission import SubmissionEvent

from ..models import EditorialAssignment, Qualification, Readiness

register = template.Library()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scipost.models import Contributor
    from submissions.models.submission import Submission


@register.simple_tag
def get_fellow_qualification(submission: "Submission", fellow: "Contributor"):
    """
    Return the Qualification for this Submission, Fellow parameters.
    """
    try:
        return submission.qualifications.get(fellow=fellow)
    except Qualification.DoesNotExist:
        return None


@register.simple_tag
def get_fellow_qualification_expertise_level_display(
    submission: "Submission", fellow: "Contributor"
):
    """
    Return the Qualification expertise_level display.
    """
    try:
        q = submission.qualifications.get(fellow=fellow)
        return q.get_expertise_level_display()
    except Qualification.DoesNotExist:
        # Try to get the Qualification from the previous Submissions
        try:
            q = Qualification.objects.filter(
                submission__in=submission.thread_full, fellow=fellow
            ).latest("submission__submission_date")
            return q.get_expertise_level_display() + " (previous submission)"
        except Qualification.DoesNotExist:
            return ""


@register.simple_tag
def get_fellow_readiness(submission: "Submission", fellow: "Contributor"):
    """
    Return the Readiness for this Submission, Fellow parameters.
    """
    try:
        return submission.readinesses.get(fellow=fellow)
    except Readiness.DoesNotExist:
        return None


@register.simple_tag
def get_fellow_readiness_status_display(
    submission: "Submission", fellow: "Contributor"
):
    """
    Return the Readiness status display for this Submission, Fellow parameters.
    """
    try:
        r = submission.readinesses.get(fellow=fellow)
        return r.get_status_display()
    except Readiness.DoesNotExist:
        # Try to get the Readiness from the previous Submissions
        try:
            q = Readiness.objects.filter(
                submission__in=submission.thread_full, fellow=fellow
            ).latest("submission__submission_date")
            return q.get_status_display() + " (previous submission)"
        except Readiness.DoesNotExist:
            return ""


@register.simple_tag
def get_annotated_submission_fellows_queryset(submission: "Submission"):
    """
    Return the fellowship of the submission with additional pool-tab-related annotations.
    """
    fellows_qs = submission.fellows.select_related_contributor__dbuser_and_profile()

    manual_eic_invitation_events = SubmissionEvent.objects.filter(
        submission=submission,
        event=EVENT_FOR_EDADMIN,
        text__icontains="manual EIC invitation",
        text__contains=Concat(
            OuterRef("contributor__profile__first_name"),
            Value(" "),
            OuterRef("contributor__profile__last_name"),
        ),
    )

    nr_manual_eic_invitations = (
        manual_eic_invitation_events.values("submission")
        .annotate(count=Count("id"))
        .values("count")[:1]
    )
    latest_manual_eic_invitation = manual_eic_invitation_events.order_by(
        "-created"
    ).values("created")[:1]

    today = timezone.now().date()
    fellows_qs = (
        fellows_qs.annotate(
            nr_manual_eic_invitations=Subquery(nr_manual_eic_invitations),
            latest_manual_eic_invitation=Subquery(latest_manual_eic_invitation),
            is_currently_available=~Exists(
                UnavailabilityPeriod.objects.filter(
                    contributor=OuterRef("contributor"),
                    start__lte=today,
                    end__gte=today,
                )
            ),
            nr_ongoing_editorial_assignments=Count(
                "contributor__editorial_assignments",
                filter=Q(
                    contributor__editorial_assignments__status=EditorialAssignment.STATUS_ACCEPTED,
                ),
            ),
            avg_overlapping_topic_weight=Subquery(
                TopicInterest.objects.filter(
                    profile=OuterRef("contributor__profile"),
                    topic__in=submission.topics.all(),
                )
                .values("profile")
                .annotate(avg_weight=Avg("weight"))
                .values("avg_weight")[:1]
            ),
        )
        .prefetch_related(
            Prefetch(
                "contributor__qualifications",
                queryset=Qualification.objects.filter(submission=submission)[:1],
                to_attr="submission_qualification",
            ),
            Prefetch(
                "contributor__readinesses",
                queryset=Readiness.objects.filter(submission=submission)[:1],
                to_attr="submission_readiness",
            ),
            Prefetch(
                "contributor__profile__submission_clearances",
                queryset=SubmissionClearance.objects.filter(submission=submission),
                to_attr="submission_clearance",
            ),
            Prefetch(
                "contributor__profile__topic_interests",
                queryset=TopicInterest.objects.filter(
                    topic__in=submission.topics.all(),
                ),
                to_attr="submission_overlapping_topics",
            ),
            Prefetch(
                "contributor__profile__conflicts_of_interest",
                queryset=ConflictOfInterest.objects.valid_on_date()
                .filter(
                    related_profile__in=submission.author_profiles.values_list(
                        "profile", flat=True
                    )
                )
                .annot_submission_exempted(submission),
                to_attr="submission_conflicts_of_interest",
            ),
            Prefetch(
                "contributor__profile__related_conflicts_of_interest",
                queryset=ConflictOfInterest.objects.valid_on_date()
                .filter(
                    profile__in=submission.author_profiles.values_list(
                        "profile", flat=True
                    )
                )
                .annot_submission_exempted(submission),
                to_attr="submission_conflicts_of_interest_related",
            ),
        )
        .order_by("contributor__profile__last_name")
    )

    return fellows_qs
