__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

import os
from typing import TYPE_CHECKING, TypeVar
from uuid import UUID
from django.core.management import BaseCommand
from django.core.serializers import serialize
from django.db.models import F, Q, Case, OuterRef, Subquery, When
from django.utils import timezone

from anonymization.models import AnonymousContributor
from journals.models.publication import Publication
from scipost.models import Contributor, Remark
from submissions.constants import EVENT_FOR_EDADMIN, EVENT_FOR_EIC
from submissions.models.assignment import EditorialAssignment
from submissions.models.communication import EditorialCommunication
from submissions.models.decision import EditorialDecision
from submissions.models.recommendation import EICRecommendation
from submissions.models.submission import Submission, SubmissionEvent, SubmissionTiering

TContributor = TypeVar("TContributor", bound=Contributor | AnonymousContributor | None)

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class Command(BaseCommand):
    help = (
        "This command replaces the authors of editorial actions "
        "with a dummy anonymous author after six months. "
        "The linking information is dumped to a backup file, "
        "and expunged from the database."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--thread_hash",
            type=str,
            help="Affect only submissions with the given thread hash.",
        )
        parser.add_argument(
            "--thread_limit",
            type=int,
            default=0,
            help="Limit the number of threads to process per run."
            "Ignored if --thread_hash is given.",
        )

    def handle(self, *args, **options):
        BACKUPS_DIR = os.environ.get("BACKUP_DIR", ".")

        this_month = timezone.datetime.now().date().replace(day=1)
        six_months_ago = (this_month - timezone.timedelta(days=180)).replace(day=1)
        filename = f"anonymized_editorial_processes_before_{six_months_ago}.json"

        latest_submissions = (
            Submission.objects.all()
            .annotate(
                completion_date_annot=Case(
                    When(
                        status=Submission.REJECTED,
                        then=Subquery(
                            EditorialDecision.objects.filter(
                                submission=OuterRef("id"),
                            ).values("taken_on")[:1]
                        ),
                    ),
                    When(
                        status=Submission.WITHDRAWN,
                        then=F("latest_activity"),
                    ),
                    default=Subquery(
                        Publication.objects.filter(
                            accepted_submission=OuterRef("id"),
                        ).values("publication_date")[:1]
                    ),
                ),
            )
            .filter(
                successor__isnull=True,
                completion_date_annot__lte=six_months_ago,
                editor_in_charge__is_anonymous=False,  # Prevent re-anonymization
            )
        )

        if thread_hash := options.get("thread_hash"):
            latest_submissions = latest_submissions.filter(thread_hash__in=thread_hash)

            if not latest_submissions.exists():
                self.stdout.write(
                    self.style.ERROR(f"Thread hash {thread_hash} not found.")
                )
                return

            filename = "anonymized_editorial_processes_for_{thread_hash}.json"
        elif thread_limit := options.get("thread_limit"):
            latest_submissions = latest_submissions[:thread_limit]

        # A dict to store the mapping of original authors to dummy authors
        # key: thread_hash, value: dict[original, anonymous]
        anonymous_map: dict[UUID, dict[Contributor, AnonymousContributor | None]] = {}

        def anon_contr_in_sub(
            contributor: AnonymousContributor | Contributor, submission: Submission
        ) -> AnonymousContributor:
            """
            Get the anonymous contributor for a given contributor in a submission.
            """
            thread_map = anonymous_map.setdefault(submission.thread_hash, {})
            if contributor.is_anonymous:
                # If the contributor is already anonymous, return it directly
                return contributor  # type: ignore

            anonymous_contributor: AnonymousContributor = thread_map.setdefault(
                contributor, contributor.anonymize().anonymous
            )  # type: ignore - Cannot be None since it was just anonymized
            return anonymous_contributor

        self.stdout.write(
            self.style.NOTICE(
                f"Submissions annotated, now starting anonymization "
                f"for {len(latest_submissions)} threads."
            )
        )

        all_submission_ids: list[int] = []
        for latest_submission in latest_submissions:
            submissions = list(
                latest_submission.thread_full.all()
                .select_related("editor_in_charge")
                .prefetch_related(
                    "editorial_assignments",
                    "eicrecommendations",
                    "eicrecommendations__remarks",
                    "eicrecommendations__eligible_to_vote",
                    "eicrecommendations__voted_for",
                    "eicrecommendations__voted_against",
                    "eicrecommendations__voted_abstain",
                    "eicrecommendations__remarks__contributor",
                    "tierings",
                    "tierings__fellow",
                )
            )
            for submission in submissions:
                all_submission_ids.append(submission.pk)
                if submission.editor_in_charge is None:
                    continue

                submission.editor_in_charge = anon_contr_in_sub(
                    submission.editor_in_charge, submission
                )

                remarks = list(submission.remarks.all())

                recommendations = list(submission.eicrecommendations.all())
                for recommendation in recommendations:
                    if recommendation.formulated_by is not None:
                        recommendation.formulated_by = anon_contr_in_sub(
                            recommendation.formulated_by, submission
                        )

                    remarks += list(recommendation.remarks.all())

                    voting_sets = [
                        "eligible_to_vote",
                        "voted_for",
                        "voted_against",
                        "voted_abstain",
                    ]
                    for voting_set in voting_sets:
                        voted_set_anon: list[AnonymousContributor] = []
                        rec_voter_set: "RelatedManager[Contributor]" = getattr(
                            recommendation, voting_set
                        )
                        for voter in rec_voter_set.all():
                            voted_set_anon.append(anon_contr_in_sub(voter, submission))

                        rec_voter_set.set(voted_set_anon)

                for remark in remarks:
                    remark.contributor = anon_contr_in_sub(
                        remark.contributor, submission
                    )

                tierings = list(submission.tierings.all())
                for tiering in tierings:
                    tiering.fellow = anon_contr_in_sub(tiering.fellow, submission)

                assignments = list(
                    submission.editorial_assignments.filter(
                        status__in=[
                            EditorialAssignment.STATUS_ACCEPTED,
                            EditorialAssignment.STATUS_COMPLETED,
                            EditorialAssignment.STATUS_DEPRECATED,
                            EditorialAssignment.STATUS_REPLACED,
                        ]
                    )
                )
                for assignment in assignments:
                    assignment.to = anon_contr_in_sub(assignment.to, submission)

                EICRecommendation.objects.bulk_update(
                    recommendations, ["formulated_by"]
                )
                SubmissionTiering.objects.bulk_update(tierings, ["fellow"])
                Remark.objects.bulk_update(remarks, ["contributor"])
                EditorialAssignment.objects.bulk_update(assignments, ["to"])

            Submission.objects.bulk_update(submissions, ["editor_in_charge"])

        all_events = (
            SubmissionEvent.objects.filter(
                submission__in=all_submission_ids,
                event__in=[EVENT_FOR_EDADMIN, EVENT_FOR_EIC],
            )
            .exclude(
                Q(text__icontains="retroactively inferred")
                | Q(text__icontains="plagiarism")
            )
            .filter(event__in=[EVENT_FOR_EDADMIN, EVENT_FOR_EIC])
        )
        all_communications = EditorialCommunication.objects.filter(
            submission__in=all_submission_ids
        )
        serialized_objects = serialize(
            "json",
            list(all_events) + list(all_communications),
        )
        with open(os.path.join(BACKUPS_DIR, filename), "w", encoding="utf-8") as f:
            f.write(serialized_objects)

        self.stdout.write(
            self.style.SUCCESS(
                f"Anonymized editorial processes for {len(all_submission_ids)} submissions "
                f"from {len(latest_submissions)} threads. "
                f"Backed up and deleted {all_events.count()} events and "
                f"{all_communications.count()} communications "
                f"to {filename}."
            )
        )

        all_events.delete()
        all_communications.delete()
