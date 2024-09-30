__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import itertools
import os

from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from django.core.serializers import serialize
from django.db.models import F, Q, Case, Exists, OuterRef, Subquery, When
from django.utils import timezone

from common.utils.text import shift_month
from journals.models.publication import Publication
from mails.models import MailLog, MailLogRelation
from submissions.constants import EIC_REC_REJECT
from submissions.models.decision import EditorialDecision
from submissions.models.referee_invitation import RefereeInvitation
from submissions.models.report import AnonymizedReportContributor, Report
from submissions.models.submission import Submission


class Command(BaseCommand):
    help = (
        "This command anonymizes the author of reports that are signed anonymously, "
        "and stores the original author information in a separate table. "
        "The table is dumped to a backup file, and the information is deleted from the database."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--report-ids",
            nargs="+",
            type=int,
            help="Anonymize reports with the given IDs.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of reports to anonymize. Ignored if --report-ids is specified.",
        )

    def handle(self, *args, **kwargs):
        BACKUPS_DIR = os.environ.get("BACKUP_DIR", ".")

        # Get all reports that are signed anonymously
        # and associated with a publication older than three months
        reports_to_anonymize = Report.objects.filter(
            anonymous=True,
            anonymized_author_table__isnull=True,
        )

        if kwargs["report_ids"]:
            reports_to_anonymize = reports_to_anonymize.filter(
                id__in=kwargs["report_ids"]
            )

            if not reports_to_anonymize.exists():
                self.stdout.write(
                    self.style.ERROR(
                        f"No reports found with the given IDs: {kwargs['report_ids']}."
                    )
                )
                return

            report_anonymization_backup_filename = (
                f"anonymized_reports_{'-'.join(map(str, kwargs['report_ids']))}.json"
            )

        else:
            now = timezone.datetime.now()
            three_months_ago = now.replace(month=shift_month(now.month, -3), day=1)
            report_anonymization_backup_filename = f"anonymized_reports_for_publications_before_{three_months_ago.strftime('%Y-%m-%d')}.json"

            reports_to_anonymize = reports_to_anonymize.annotate(
                processing_date=Case(
                    When(
                        submission__status=Submission.REJECTED,
                        then=Subquery(
                            EditorialDecision.objects.filter(
                                submission=OuterRef("submission"),
                            ).values("taken_on")[:1]
                        ),
                    ),
                    When(
                        submission__status=Submission.WITHDRAWN,
                        then=F("submission__latest_activity"),
                    ),
                    default=Subquery(
                        Publication.objects.filter(
                            accepted_submission__thread_hash=OuterRef(
                                "submission__thread_hash"
                            )
                        ).values("publication_date")[:1]
                    ),
                )
            ).filter(processing_date__lte=three_months_ago)

            if limit := kwargs.get("limit", 0):
                reports_to_anonymize = reports_to_anonymize[:limit]

        if not reports_to_anonymize.exists():
            self.stdout.write(self.style.WARNING(f"No reports found to anonymize."))
            return

        report_anonymization_backup_path = os.path.join(
            BACKUPS_DIR, "anonymized_reports", report_anonymization_backup_filename
        )
        if os.path.exists(report_anonymization_backup_path):
            self.stdout.write(
                self.style.ERROR(
                    f"Backup file {report_anonymization_backup_path} already exists."
                )
            )
            return

        # Construct a report filter of including both the last name of the author
        # and the report's submission title in the body of a MailLog
        mentions_referee_and_submission = Q()
        for report in reports_to_anonymize:
            author = report.real_author or report.author
            author = author.profile or author.user
            mentions_referee_and_submission |= Q(body__contains=author.last_name) & Q(
                body__contains=report.submission.title
            )

        # Unpack the updated objects into model-specific lists
        ARCs, reports, invitations = zip(
            *[
                report.anonymize_author_long_term(commit=False)
                for report in reports_to_anonymize
            ]
        )
        invitations = list(itertools.chain.from_iterable(invitations))

        # Bulk-update the ARCs, reports, and invitations since commit=False
        AnonymizedReportContributor.objects.bulk_update(
            ARCs,
            ["anonymized_author", "original_author", "invitation_email"],
        )
        Report.objects.bulk_update(reports, ["author"])
        RefereeInvitation.objects.bulk_update(
            invitations,
            ["referee", "email_address"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Anonymized {len(reports_to_anonymize)} reports "
                f"and {len(invitations)} refereeing invitations."
            )
        )

        # Reconstruct a queryset of the ARCs to serialize and delete
        ARCs = AnonymizedReportContributor.objects.filter(
            pk__in=[arc.pk for arc in ARCs]
        )

        # Get all emails related to the reports or invitations that were anonymized
        related_emails = MailLog.objects.annotate(
            has_report_in_context=Exists(
                MailLogRelation.objects.filter(
                    mail=OuterRef("pk"),
                    content_type=ContentType.objects.get_for_model(Report),
                    object_id__in=[report.id for report in reports],
                )
            ),
            has_referee_invitation_in_context=Exists(
                MailLogRelation.objects.filter(
                    mail=OuterRef("pk"),
                    content_type=ContentType.objects.get_for_model(RefereeInvitation),
                    object_id__in=[invitation.id for invitation in invitations],
                )
            ),
        ).filter(
            Q(has_report_in_context=True)
            | Q(has_referee_invitation_in_context=True)
            | mentions_referee_and_submission
        )

        self.stdout.write(
            self.style.NOTICE(
                (
                    f"Laboriously determining related emails ... "
                    "This may take a while."
                )
            )
        )

        # Serialize the ARCs and related emails
        # and write them to a backup file
        serialized_ARCs = serialize(
            "json",
            ARCs,
            fields=[
                "anonymized_author",
                "original_author",
                "invitation_email",
            ],
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
            # Hacky way to concatenate the two JSON arrays in string form
            f.write(serialized_ARCs[:-1] + "," + serialized_emails[1:])

        # Finally, delete the information tables and all related emails
        ARCs.update(
            anonymized_author=None,
            original_author=None,
            invitation_email="",
        )
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
            created=timezone.datetime(1970, 1, 1, tzinfo=timezone.utc),
            latest_activity=timezone.datetime(1970, 1, 1, tzinfo=timezone.utc),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Dumped {len(reports_to_anonymize)} report authors and their {deleted_mail_count} related emails to "
                f"{report_anonymization_backup_path}, and deleted the information from the database."
            )
        )
