__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from collections.abc import Callable
from itertools import chain, groupby
from guardian.shortcuts import get_objects_for_user

from django.core.management import BaseCommand
from django.db.models import Model, QuerySet

from colleges.models import Fellowship, FellowshipNominationVotingRound
from comments.models import Comment
from mails.utils import DirectMailUtil

from submissions.models import EICRecommendation, Submission, Report

from typing import Any, TypeVar

M = TypeVar("M", bound=Model)

class Command(BaseCommand):
    """Send out mail to Fellows letting them know about their open tasks."""

    help = "Sends an email to Fellows with current and upcoming tasks list"

    def handle(self, *args, **kwargs):
        fellowships = Fellowship.objects.active()
        count = 0

        ##### Handle comments awaiting vetting
        comments_awaiting_vetting = Comment.objects.all().awaiting_vetting()
        comment_content_types: list[int] = list(
            comments_awaiting_vetting.order_by("content_type")
            .values_list("content_type", flat=True)
            .distinct()
        )

        # Handle comments by content type: comments attached to either a Submission or a Report
        # are filtered out if the latest Submission in the thread has been treated.
        CONTENT_TYPE_GROUPERS: dict[int, Callable[[Comment], Any] | None] = {
            16: lambda c: c.content_object.thread_hash,  # Submission
            17: lambda c: c.content_object.submission.thread_hash,  # Report
        }

        for content_type_id in comment_content_types:
            CONTENT_TYPE_GROUPERS.setdefault(content_type_id, None)

        def get_objects_to_vet(
            qs: QuerySet[M], grouper: Callable[[M], Any] | None = None
        ):
            objects: list[M] = list(qs)
            if not grouper:
                return objects

            objects_to_vet: list[M] = []
            for thread_hash, thread in groupby(
                sorted(objects, key=grouper), key=grouper
            ):
                latest_submission = (
                    Submission.objects.filter(thread_hash=thread_hash)
                    .order_by("-id")
                    .first()
                )
                if latest_submission and latest_submission.treated:
                    continue

                objects_to_vet.extend(list(thread))
            return objects_to_vet

        reports_awaiting_vetting = (
            Report.objects.awaiting_vetting()
            .select_related("submission")
            .order_by("submission__thread_hash", "submission__id")
        )

        ##### Handle comments awaiting vetting
        for fellowship in fellowships:
            comments_can_vet: QuerySet[Comment] = get_objects_for_user(
                fellowship.contributor.user,
                "comments.can_vet_comments",
                klass=comments_awaiting_vetting,
            )
            comments_to_vet = list(
                chain.from_iterable(
                    get_objects_to_vet(ct_comments, grouper)
                    for ct_id, grouper in CONTENT_TYPE_GROUPERS.items()
                    if (ct_comments := comments_can_vet.filter(content_type__id=ct_id))
                )
            )

            reports_can_vet: QuerySet[Report] = reports_awaiting_vetting.filter(
                submission__editor_in_charge=fellowship.contributor
            )
            reports_to_vet = get_objects_to_vet(
                reports_can_vet, lambda r: r.submission.thread_hash
            )

            nr_nominations_to_vote_on = (
                FellowshipNominationVotingRound.objects.ongoing()
                .filter(eligible_to_vote=fellowship)
                .exclude(votes__fellow=fellowship)
                .count()
            )
            visible_in_pool = (
                fellowship.pool.all()
                .in_pool(fellowship.contributor.user)
                .filter(status=Submission.SEEKING_ASSIGNMENT)
            )
            nr_visible = visible_in_pool.count()
            nr_appraised = (
                visible_in_pool.annot_fully_appraised_by(fellowship.contributor)
                .filter(is_fully_appraised=True)
                .count()
            )
            recs_to_vote_on = EICRecommendation.objects.user_must_vote_on(
                fellowship.contributor.user
            )
            assignments_ongoing = fellowship.contributor.editorial_assignments.ongoing()
            assignments_ongoing_with_required_actions = (
                assignments_ongoing.with_required_actions()
            )
            assignments_to_consider = (
                fellowship.contributor.editorial_assignments.invited()
            )
            assignments_upcoming_deadline = (
                assignments_ongoing.refereeing_deadline_within(days=7)
            )
            if (
                recs_to_vote_on
                or assignments_ongoing_with_required_actions
                or assignments_to_consider
                or assignments_upcoming_deadline
                or nr_visible > nr_appraised
                or comments_to_vet
                or reports_to_vet
            ):
                DirectMailUtil(
                    "fellows/email_fellow_tasklist",
                    # Render immediately, because m2m/querysets cannot be saved for later rendering:
                    delayed_processing=False,
                    fellow=fellowship.contributor,
                    nr_nominations_to_vote_on=nr_nominations_to_vote_on,
                    recs_to_vote_on=recs_to_vote_on,
                    assignments_ongoing=assignments_ongoing,
                    assignments_to_consider=assignments_to_consider,
                    nr_visible=nr_visible,
                    nr_appraised=nr_appraised,
                    nr_appraisals_required=(nr_visible - nr_appraised),
                    assignments_upcoming_deadline=assignments_upcoming_deadline,
                    comments_to_vet=comments_to_vet,
                    reports_to_vet=reports_to_vet,
                ).send_mail()
                count += 1
        self.stdout.write(self.style.SUCCESS("Emailed {} fellows.".format(count)))
