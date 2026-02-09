__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"

from functools import reduce
from itertools import groupby
import os
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, TypeVar
from uuid import UUID

from django.core.management import BaseCommand
from django.core.serializers import serialize
from django.db.models import F, Q, Case, OuterRef, Prefetch, Subquery, When
from django.utils import timezone
from tqdm import tqdm

from anonymization.models import (
    AnonymousContributor,
    ContributorAnonymization,
    ProfileAnonymization,
)
from ethics.models import GenAIDisclosure
from journals.models.publication import Publication
from mails.models import MailLog, MailLogRelation
from profiles.models import Profile
from scipost.models import Contributor, Remark
from scipost.utils import ContributorStatsAccessor
from submissions.constants import EVENT_FOR_EDADMIN, EVENT_FOR_EIC
from submissions.models.assignment import EditorialAssignment
from submissions.models.communication import EditorialCommunication
from submissions.models.decision import EditorialDecision
from submissions.models.recommendation import EICRecommendation
from submissions.models.referee_invitation import RefereeInvitation
from submissions.models.report import Report
from submissions.models.submission import Submission, SubmissionEvent, SubmissionTiering

TContributor = TypeVar("TContributor", bound=Contributor | AnonymousContributor | None)

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


# A dict to map original authors to dummy authors per submission thread
# key: original, value: dict[thread_hash, anonymous]
anonymous_map: dict[Contributor, dict[UUID, AnonymousContributor]] = {}
thread_anonymization_contributors: dict[UUID, list[ContributorAnonymization]] = {}
thread_anonymization_profiles: dict[UUID, list[ProfileAnonymization]] = {}


def anon_contr_in_sub(
    contributor: AnonymousContributor | Contributor, submission: Submission
) -> AnonymousContributor:
    """
    Return the anonymous contributor for a given contributor in a submission.
    Also save the anonymization for later serialization.
    """
    hash = submission.thread_hash
    anon_contrib_map = anonymous_map.setdefault(contributor, {})

    # If the contributor is already anonymous, or if there exists
    # an anonymized version for this thread, return it directly
    if contributor.is_anonymous:
        return contributor  # type: ignore
    elif anonymous_contributor := anon_contrib_map.get(hash):
        return anonymous_contributor

    contributor_anonymization = contributor.anonymize()
    thread_anonymization_contributors.setdefault(hash, []).append(
        contributor_anonymization
    )
    anonymous_contributor = contributor_anonymization.anonymous

    # It is possible that the contributor doesn't have a profile.
    # For these cases, guard against it not having an eponymization.
    if contributor.profile:
        thread_anonymization_profiles.setdefault(hash, []).append(
            contributor_anonymization.anonymous.profile.eponymization  # type: ignore
        )

    # Cache the anonymous contributor in the map
    anon_contrib_map[hash] = anonymous_contributor  # type: ignore

    return anonymous_contributor  # type: ignore


class Command(BaseCommand):
    help = (
        "This command replaces the authors of editorial actions "
        "with a dummy anonymous author after some time. "
        "Related objects such as emails, events, and remarks "
        "are serialized and dumped to a JSON file before deletion. "
        "The command can be run with --thread_hash to anonymize a specific thread, "
        "or with --thread_limit to limit the number of threads processed per run. "
        "If neither is specified, it will anonymize all threads. "
        "Editorial processes to be anonymized are: "
        "editor in charge, assignments, recommendations, "
        "remarks, tierings, votes, events, communications, "
        "referee reports and invitations."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--thread_hash",
            type=str,
            nargs="+",
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
        DUMP_FILENAME_TEMPLATE = "anonymized_editorial_processes_{hash}.json"

        BACKUPS_DIR = Path(os.environ.get("BACKUP_DIR", "."))
        ANON_BACKUPS_DIR = BACKUPS_DIR / "anonymized" / "editorial_processes"
        os.makedirs(ANON_BACKUPS_DIR, exist_ok=True)

        # Fetch all threads that have submissions with a status that requires anonymization
        # and that have a completion date older than six months.
        latest_submission_threads = (
            Submission.objects.all()
            .annotate(
                completion_date_annot=Case(
                    When(
                        status=Submission.REJECTED,
                        then=Subquery(
                            EditorialDecision.objects.filter(
                                submission=OuterRef("id"),
                                status=EditorialDecision.FIXED_AND_ACCEPTED,
                            ).values("taken_on")[:1]
                        ),
                    ),
                    When(
                        status=Submission.WITHDRAWN,
                        then=Subquery(
                            SubmissionEvent.objects.filter(
                                submission=OuterRef("id"),
                                text__contains="withdrawn",
                            ).values("created")[:1]
                        ),
                    ),
                    When(
                        status=Submission.PUBLISHED,
                        then=Subquery(
                            Publication.objects.filter(
                                accepted_submission=OuterRef("id"),
                            ).values("publication_date")[:1]
                        ),
                    ),
                    default=None,
                ),
            )
            .filter(
                Q(status=Submission.REJECTED)
                | Q(status=Submission.WITHDRAWN)
                | Q(status=Submission.PUBLISHED),
                completion_date_annot__isnull=False,
                completion_date_annot__lte=timezone.now(),
                editor_in_charge__is_anonymous=False,  # Prevent re-anonymization
            )
            .values("thread_hash")
        )

        # Filter the submissions based on the command options:
        # - If `thread_hash` is provided, filter submissions by that thread hash.
        # - If `thread_limit` is provided, limit the number of threads processed.
        if thread_hashes := options.get("thread_hash"):
            latest_submission_threads = latest_submission_threads.filter(
                thread_hash__in=thread_hashes
            )
        elif thread_limit := options.get("thread_limit"):
            latest_submission_threads = latest_submission_threads[:thread_limit]

        nr_threads_to_process = latest_submission_threads.count()

        # Fetch all submissions that are part of the threads that need anonymization
        # and prefetch related objects to avoid N+1 queries.
        submissions = (
            Submission.objects.all()
            .filter(thread_hash__in=latest_submission_threads)
            .select_related("editor_in_charge")
            .prefetch_related(
                "editorial_assignments",
                Prefetch(
                    "eicrecommendations",
                    queryset=EICRecommendation.objects.prefetch_related(
                        "gen_ai_disclosures",
                        "eligible_to_vote",
                        "voted_for",
                        "voted_against",
                        "voted_abstain",
                        "remarks",
                        "remarks__contributor",
                    ),
                ),
                "editorial_communications",
                "tierings",
                "tierings__fellow",
                "referee_invitations",
                Prefetch(
                    "reports",
                    queryset=Report.objects.all()
                    .filter(anonymous=True)  # Only fetch anonymous reports
                    .prefetch_related("gen_ai_disclosures"),
                ),
                Prefetch(
                    "events",
                    queryset=SubmissionEvent.objects.filter(
                        Q(event=EVENT_FOR_EDADMIN) | Q(event=EVENT_FOR_EIC)
                    ).exclude(
                        Q(text__icontains="retroactively inferred")
                        | Q(text__icontains="plagiarism")
                    ),
                    to_attr="eic_events",
                ),
            )
            .order_by("thread_hash", "id")
        )

        if not submissions.exists():
            self.stdout.write(self.style.WARNING(f"No submissions found to anonymize."))
            return

        # ====================================================
        # Create anonymous replacements for each contributor
        # across all submissions in the thread and
        # anonymize their contributions (eic, votes, remarks, etc.)
        # ====================================================

        # Store each contributor only once per their PK
        # such that their stats can accumulate deltas
        contributors_stats: dict[int, ContributorStatsAccessor] = {}

        nr_objects_processed = {
            "submissions": 0,
            "reports": 0,
            "invitations": 0,
            "recommendations": 0,
            "tierings": 0,
            "remarks": 0,
            "assignments": 0,
            "events": 0,
            "communications": 0,
            "gen_ai_disclosures": 0,
            "emails": 0,
            "email_relations": 0,
        }
        submissions = list(submissions)
        pbar = tqdm(
            groupby(submissions, key=lambda s: s.thread_hash),
            total=nr_threads_to_process,
            unit="thread",
        )
        for thread_hash, thread in pbar:
            pbar.set_description(f"Anonymizing thread {thread_hash}")

            thread_events: list[SubmissionEvent] = []
            thread_communications: list[EditorialCommunication] = []
            thread_emails: list[MailLog] = []
            thread_invitations: list[RefereeInvitation] = []

            # Determine the filename for the backup of a given thread
            # Skip it if the file already exists
            filename = DUMP_FILENAME_TEMPLATE.format(hash=thread_hash)
            if (ANON_BACKUPS_DIR / filename).exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"Backup file {ANON_BACKUPS_DIR / filename} already exists. "
                        "Stopping to avoid overwriting."
                    )
                )
                continue

            for sub_order, submission in enumerate(thread):
                # Guard against submissions without an editor in charge
                # (should never happen, mostly for static type checking)
                if submission.editor_in_charge is None:
                    continue

                # Create a list of profiles for the submission to be used when
                # filtering the MailLog entries.
                submission_profiles: list[Profile | None] = []

                # Heuristically determine the completed date for the assignment
                # To be used as the subgroup year of EIC assignment stats
                if completed_assignment := (
                    submission.editorial_assignments.filter(
                        status=EditorialAssignment.STATUS_COMPLETED,
                        to=submission.editor_in_charge,
                    ).first()
                ):
                    completed_date = completed_assignment.date_answered
                elif assignment_event := submission.events.filter(
                    text__icontains="has been assigned"
                ).first():
                    completed_date = assignment_event.created
                elif submission.eic_first_assigned_date:
                    completed_date = submission.eic_first_assigned_date
                else:
                    completed_date = submission.latest_activity

                editor_stats = contributors_stats.setdefault(
                    submission.editor_in_charge.pk,
                    submission.editor_in_charge.stats,
                )
                editor_stats.increment_anon(
                    "nr_assignments_completed",
                    subgroup=completed_date.year,
                )

                if sub_order == 0:
                    # Increment the thread-level assignment stat
                    # using the assignment date of the original version
                    editor_stats.increment_anon(
                        "nr_thread_assignments_completed",
                        subgroup=completed_date.year,
                    )

                submission.editor_in_charge = anon_contr_in_sub(
                    submission.editor_in_charge, submission
                )
                # No need to add EIC to the mail log query list since
                # they will be added during editorial assignments/votes

                gen_ai_disclosures: list[GenAIDisclosure] = []
                remarks = list(submission.remarks.all())
                recommendations = list(submission.eicrecommendations.all())
                for recommendation in recommendations:
                    # Append recommendation remarks to submission remarks
                    remarks.extend(list(recommendation.remarks.all()))

                    rec_author_anon = None
                    rec_author_original = None
                    if recommendation.formulated_by is not None:
                        # No need to put original in submission_profiles,
                        # since it'll be added during vote eligibility
                        rec_author_original = recommendation.formulated_by
                        rec_author_anon = anon_contr_in_sub(
                            rec_author_original, submission
                        )
                        recommendation.formulated_by = rec_author_anon

                        for disclosure in recommendation.gen_ai_disclosures.all():
                            disclosure.contributor = rec_author_anon
                            gen_ai_disclosures.append(disclosure)

                    # Anonymize all voting contributors for each
                    # of the voting sets of a recommendation
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
                            voter_stats = contributors_stats.setdefault(
                                voter.pk, voter.stats
                            )
                            if voting_set == "eligible_to_vote":
                                # Append the profile only for eligible voters
                                # and therefore avoiding duplicates
                                submission_profiles.append(voter.profile)
                                voter_stats.increment_anon(
                                    "nr_recommendations_eligible",
                                    subgroup=recommendation.date_submitted.year,
                                )
                            else:  # voted for, against, abstained
                                voter_stats.increment_anon(
                                    "nr_recommendations_voted",
                                    subgroup=recommendation.date_submitted.year,
                                )

                            voted_set_anon.append(anon_contr_in_sub(voter, submission))

                        rec_voter_set.set(voted_set_anon)

                for remark in remarks:
                    # These profiles should have already been added during vote eligibility
                    remark.contributor = anon_contr_in_sub(
                        remark.contributor, submission
                    )

                tierings = list(submission.tierings.all())
                for tiering in tierings:
                    # Ditto
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
                    submission_profiles.append(assignment.to.profile)
                    assignment.to = anon_contr_in_sub(assignment.to, submission)

                # Anonymize anonymous reports and their invitations
                related_invitations = list(
                    submission.referee_invitations.all()
                    .filter(referee__in=submission.reports.values("author__profile"))
                    .select_related("referee")
                    .order_by("referee_id")
                )
                # Submission reports loaded in the prefetch as filtered to Anonymous only
                reports = list(submission.reports.all())
                for report in reports:
                    author_stats = contributors_stats.setdefault(
                        report.author.pk,
                        report.author.stats,
                    )
                    author_stats.increment_anon(
                        "nr_reports_authored",
                        subgroup=report.date_submitted.year,
                    )
                    anon_report_author = anon_contr_in_sub(report.author, submission)
                    for disclosure in report.gen_ai_disclosures.all():
                        disclosure.contributor = anon_report_author
                        gen_ai_disclosures.append(disclosure)
                    for invitation in related_invitations:
                        if (
                            # Important to check here again, because
                            # we'll be reusing `author_stats`
                            invitation.referee == report.author.profile
                            and invitation.date_invited
                        ):
                            author_stats.increment_anon(
                                "nr_referee_invited",
                                subgroup=invitation.date_invited.year,
                            )

                            if invitation.cancelled:
                                invitation_status = "cancelled"
                            elif invitation.fulfilled:
                                invitation_status = "fulfilled"
                            elif invitation.accepted is None:
                                invitation_status = "pending"
                            elif invitation.accepted:
                                invitation_status = "accepted"
                            elif not invitation.accepted:
                                invitation_status = "declined"
                            else:
                                invitation_status = "unknown"

                            author_stats.increment_anon(
                                f"nr_referee_{invitation_status}",
                                subgroup=invitation.date_invited.year,
                            )

                            # Since the report author is the referee of the invitation,
                            # anonymize the invitation reusing the anon profile
                            invitation.referee = anon_report_author.profile  # type: ignore
                    report.author = anon_report_author

                # After having anonymized everything, dump objects with
                # total or partial information deletion
                submission_profile_Qs = [
                    Q(body__icontains=profile.last_name)
                    for profile in submission_profiles
                    if profile is not None
                ]
                if not submission_profile_Qs:
                    submission_profile_Qs.append(Q(pk__isnull=True))  # No matches

                thread_emails.extend(
                    list(
                        MailLog.objects.filter(
                            reduce(lambda x, y: x | y, submission_profile_Qs),
                            body__icontains=submission.title,
                        )
                    )
                )
                thread_events.extend(submission.eic_events)
                thread_invitations.extend(related_invitations)
                thread_communications.extend(
                    list(submission.editorial_communications.all())
                )

                # Bulk update all anonymized contributors of related objects
                nr_reports_processed = Report.objects.bulk_update(reports, ["author"])
                nr_invitations_processed = RefereeInvitation.objects.bulk_update(
                    related_invitations, ["referee"]
                )
                nr_recommendations_processed = EICRecommendation.objects.bulk_update(
                    recommendations, ["formulated_by"]
                )
                nr_tierings_processed = SubmissionTiering.objects.bulk_update(
                    tierings, ["fellow"]
                )
                nr_remarks_processed = Remark.objects.bulk_update(
                    remarks, ["contributor"]
                )
                nr_assignments_processed = EditorialAssignment.objects.bulk_update(
                    assignments, ["to"]
                )
                nr_gen_ai_disclosures_processed = GenAIDisclosure.objects.bulk_update(
                    gen_ai_disclosures, ["contributor"]
                )

                # Update all counts
                nr_objects_processed["submissions"] += 1
                nr_objects_processed["reports"] += nr_reports_processed
                nr_objects_processed["invitations"] += nr_invitations_processed
                nr_objects_processed["recommendations"] += nr_recommendations_processed
                nr_objects_processed["tierings"] += nr_tierings_processed
                nr_objects_processed["remarks"] += nr_remarks_processed
                nr_objects_processed["assignments"] += nr_assignments_processed
                nr_objects_processed["gen_ai_disclosures"] += (
                    nr_gen_ai_disclosures_processed
                )

            # Remove duplicates from the thread email logs
            thread_emails = list(set(thread_emails))
            thread_email_relations = list(
                MailLogRelation.objects.filter(mail__in=[o.id for o in thread_emails])
            )

            serialized_objects = serialize(
                "json",
                thread_anonymization_contributors.get(thread_hash, [])
                + thread_anonymization_profiles.get(thread_hash, [])
                + thread_events
                + thread_communications
                + thread_invitations
                + thread_emails
                + thread_email_relations,
            )

            with open(ANON_BACKUPS_DIR / filename, "w", encoding="utf-8") as f:
                f.write(serialized_objects)

            # Delete any related objects to be purged completely
            nr_events_processed, _ = SubmissionEvent.objects.filter(
                pk__in=[o.pk for o in thread_events]
            ).delete()
            nr_communications_processed, _ = EditorialCommunication.objects.filter(
                pk__in=[o.pk for o in thread_communications]
            ).delete()
            nr_email_relations_processed, _ = MailLogRelation.objects.filter(
                pk__in=[o.pk for o in thread_email_relations]
            ).delete()
            nr_emails_processed, _ = MailLog.objects.filter(
                pk__in=[o.pk for o in thread_emails]
            ).delete()

            nr_objects_processed["events"] += nr_events_processed
            nr_objects_processed["communications"] += nr_communications_processed
            nr_objects_processed["email_relations"] += nr_email_relations_processed
            nr_objects_processed["emails"] += nr_emails_processed

            # Update the invitations again to clear out the email
            # Only safe to do this after serializing the objects
            RefereeInvitation.objects.filter(
                pk__in=[o.pk for o in thread_invitations]
            ).update(email_address="")

            # Purge the original contributor/profile from the anonymizations
            ContributorAnonymization.objects.filter(
                pk__in=[o.pk for o in thread_anonymization_contributors[thread_hash]]
            ).update(original="")
            ProfileAnonymization.objects.filter(
                pk__in=[o.pk for o in thread_anonymization_profiles[thread_hash]]
            ).update(original="")

            pbar.set_postfix(nr_objects_processed)

        Submission.objects.bulk_update(submissions, ["editor_in_charge"])

        # Save the anonymous stats for each contributor
        # from the accumulated deltas
        for contributor_stat in contributors_stats.values():
            contributor_stat.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Anonymized editorial processes for {len(submissions)} submissions "
                f"from {nr_threads_to_process} threads. "
                f"Backed up and deleted: "
                f"{nr_objects_processed['submissions']} submissions, "
                f"{nr_objects_processed['reports']} reports, "
                f"{nr_objects_processed['invitations']} invitations, "
                f"{nr_objects_processed['recommendations']} recommendations, "
                f"{nr_objects_processed['tierings']} tierings, "
                f"{nr_objects_processed['remarks']} remarks, "
                f"{nr_objects_processed['assignments']} assignments, "
                f"{nr_objects_processed['events']} events, "
                f"{nr_objects_processed['communications']} communications, "
                f"{nr_objects_processed['gen_ai_disclosures']} gen_ai_disclosures, "
                f"{nr_objects_processed['emails']} emails, and "
                f"{nr_objects_processed['email_relations']} email relations."
            )
        )
