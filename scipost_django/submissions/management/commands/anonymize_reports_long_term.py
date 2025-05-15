__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


from functools import reduce
import os
from uuid import UUID

from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.core.serializers import serialize
from django.db.models import F, Q, Case, Exists, OuterRef, Subquery, When
from django.utils import timezone

from anonymization.models import (
    AnonymousContributor,
    ContributorAnonymization,
    ProfileAnonymization,
)
from journals.models.publication import Publication
from mails.models import MailLog, MailLogRelation
from scipost.models import Contributor
from submissions.models.decision import EditorialDecision
from submissions.models.referee_invitation import RefereeInvitation
from submissions.models.report import Report
from submissions.models.submission import Submission


class Command(BaseCommand):
    help = (
        "This command replaces the authors of anonymous reports "
        "with a dummy anonymous author after three months. "
        "The linking information is dumped to a backup file, "
        "and the expunged from the database."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--thread_hash",
            type=str,
            help="Anonymize reports for submissions with the given thread hash.",
        )
        parser.add_argument(
            "--thread_limit",
            type=int,
            help="Limit the number of threads to anonymize reports for. Ignored if --thread_hash is specified.",
        )

    def handle(self, *args, **kwargs):
        BACKUPS_DIR = os.environ.get("BACKUP_DIR", ".")

        # Get all reports that are signed anonymously
        # and are not already anonymized
        reports_to_anonymize = Report.objects.filter(
            author__is_anonymous=False, anonymous=True
        )

        now = timezone.datetime.now().date()
        three_months_ago = (now - timezone.timedelta(days=90)).replace(day=1)
        report_anonymization_backup_filename = f"anonymized_reports_for_publications_before_{three_months_ago.strftime('%Y-%m-%d')}.json"

        if thread_hash := kwargs.get("thread_hash"):
            reports_to_anonymize = reports_to_anonymize.filter(
                submission__thread_hash__in=thread_hash
            )

            if not reports_to_anonymize.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"No reports found related to the thread hash: {thread_hash}"
                    )
                )
                return

            report_anonymization_backup_filename = (
                f"anonymized_reports_for_{thread_hash}.json"
            )
        elif thread_limit := kwargs.get("thread_limit", 0):
            # We need to fetch the threads first and subsequently filter the reports
            thread_hashes = reports_to_anonymize.values(
                "submission__thread_hash"
            ).distinct()[:thread_limit]
            reports_to_anonymize = reports_to_anonymize.filter(
                submission__thread_hash__in=thread_hashes
            )

        # If no thread hash is provided, we will anonymize all reports
        reports_to_anonymize = reports_to_anonymize.annotate(
            latest_status=Subquery(
                Submission.objects.filter(
                    thread_hash=OuterRef("submission__thread_hash")
                )
                .order_by("-submission_date")
                .values("status")[:1]
            ),
            processing_date=Case(
                When(
                    latest_status=Submission.REJECTED,
                    then=Subquery(
                        EditorialDecision.objects.filter(
                            submission=OuterRef("submission"),
                        ).values("taken_on")[:1]
                    ),
                ),
                When(
                    latest_status=Submission.WITHDRAWN,
                    then=F("submission__latest_activity"),
                ),
                default=Subquery(
                    Publication.objects.filter(
                        accepted_submission__thread_hash=OuterRef(
                            "submission__thread_hash"
                        )
                    ).values("publication_date")[:1]
                ),
            ),
        ).filter(processing_date__lte=three_months_ago)

        if not reports_to_anonymize.exists():
            self.stdout.write(self.style.WARNING(f"No reports found to anonymize."))
            return

        os.makedirs(os.path.join(BACKUPS_DIR, "anonymized_reports"), exist_ok=True)
        report_anonymization_backup_path = os.path.join(
            BACKUPS_DIR, "anonymized_reports", report_anonymization_backup_filename
        )
        if os.path.exists(report_anonymization_backup_path):
            self.stdout.write(
                self.style.ERROR(
                    f"Backup file {report_anonymization_backup_path} already exists. "
                    "Stopping to avoid overwriting."
                )
            )
            return

        # ====================================================
        # Create anonymous replacements for each report author
        # across all submissions in the thread
        # and anonymize the reports and invitations
        # ====================================================

        # We need to use a dict to avoid duplicate UUIDs
        # as a dict (thread_hash, author) -> anonymous_contributor
        anonymization_uuids: dict[tuple[UUID, Contributor], AnonymousContributor] = {}

        # Also, construct a filter to include both the last name of the author
        # and the report's submission title in the body of a MailLog
        mlog_filter: list[Q] = []

        # Fetch reports and downcast to list
        reports_to_anonymize = list(reports_to_anonymize)
        for report in reports_to_anonymize:
            # Guard unlikely scenario where the author doesn't have a profile
            if (profile := report.author.profile) is None:
                continue

            # Add a possible matching set for related mail logs
            mlog_filter.append(
                Q(body__contains=profile.last_name)
                & Q(body__contains=report.submission.title)
            )

            hash_contributor_key = (report.submission.thread_hash, report.author)
            if anonymous_contributor := anonymization_uuids.get(
                hash_contributor_key,
                report.author.anonymize().anonymous,
            ):
                report.author = anonymous_contributor

                # Add to dict to avoid duplicate anonymizations
                anonymization_uuids[hash_contributor_key] = anonymous_contributor

        Report.objects.bulk_update(reports_to_anonymize, ["author"])

        # Clean out related information in the invitation table
        #! This is assuming that the referees don't have both anonymous and eponymoush reports
        #! In the contrary case, even the eponymous invitations will be anonymized
        invitation_ids: list[int] = []
        for (thread_hash, author), anonymous_contributor in anonymization_uuids.items():
            related_invitations = RefereeInvitation.objects.filter(
                submission__thread_hash=thread_hash, referee=author.profile
            )
            related_invitations.update(
                referee=anonymous_contributor.profile, email_address=""
            )
            invitation_ids.extend(related_invitations.values_list("id", flat=True))

        # The total filter is an OR of all the individual mail log filtering conditions
        mentions_referee_and_submission = reduce(lambda x, y: x | y, mlog_filter, Q())

        self.stdout.write(
            self.style.SUCCESS(
                f"Anonymized {len(reports_to_anonymize)} reports "
                f"and related refereeing invitations."
            )
        )

        # Get all emails related to the reports or invitations that were anonymized
        related_emails = MailLog.objects.annotate(
            has_report_in_context=Exists(
                MailLogRelation.objects.filter(
                    mail=OuterRef("pk"),
                    content_type=ContentType.objects.get_for_model(Report),
                    object_id__in=[report.id for report in reports_to_anonymize],
                )
            ),
            has_referee_invitation_in_context=Exists(
                MailLogRelation.objects.filter(
                    mail=OuterRef("pk"),
                    content_type=ContentType.objects.get_for_model(RefereeInvitation),
                    object_id__in=invitation_ids,
                )
            ),
        ).filter(
            Q(has_report_in_context=True)
            | Q(has_referee_invitation_in_context=True)
            | mentions_referee_and_submission
        )

        self.stdout.write(
            self.style.NOTICE(
                (f"Laboriously determining related emails ... This may take a while.")
            )
        )

        profile_anonymizations = [
            a.profile.eponymization
            for a in anonymization_uuids.values()
            if a.profile and a.profile.eponymization
        ]
        contributor_anonymizations = [
            a.eponymization for a in anonymization_uuids.values() if a.eponymization
        ]

        serialized_profile_anonymizations = serialize(
            "json",
            profile_anonymizations,
            fields=["uuid", "original", "anonymous"],
        )
        serialized_contributor_anonymizations = serialize(
            "json",
            contributor_anonymizations,
            fields=["uuid", "original", "anonymous"],
        )

        serialized_emails = serialize(
            "json",
            related_emails,
            fields=[
                "subject",
                "mail_code",
                "body",
                "body_html",
                "from_email",
                "sent_to",
                "to_recipients",
                "cc_recipients",
                "bcc_recipients",
                "created",
                "latest_activity",
            ],
        )

        with open(report_anonymization_backup_path, "w") as f:
            # Hacky way to concatenate the JSON arrays in string form
            f.write(
                serialized_profile_anonymizations[:-1]
                + ","
                + serialized_contributor_anonymizations[1:-1]
                + ","
                + serialized_emails[1:]
            )

        # Finally, delete the information tables and all related emails
        for ca in contributor_anonymizations:
            ca.original = None
        for pa in profile_anonymizations:
            pa.original = None

        ContributorAnonymization.objects.bulk_update(
            contributor_anonymizations, ["original"]
        )
        ProfileAnonymization.objects.bulk_update(profile_anonymizations, ["original"])

        deleted_mail_count = related_emails.update(
            subject="",
            mail_code="",
            body="",
            body_html="",
            from_email="",
            sent_to=[],
            to_recipients=[],
            cc_recipients=[],
            bcc_recipients=[],
            created=timezone.datetime(1970, 1, 1),
            latest_activity=timezone.datetime(1970, 1, 1),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Dumped {len(reports_to_anonymize)} report authors and their {deleted_mail_count} related emails to "
                f"{report_anonymization_backup_path}, and deleted the information from the database."
            )
        )
