__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import itertools
import os

from django.core.management import BaseCommand
from django.core.serializers import deserialize
from submissions.models.referee_invitation import RefereeInvitation
from submissions.models.report import AnonymizedReportContributor, Report


class Command(BaseCommand):
    help = "Restore report information from long-term storage."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--backup-file",
            type=str,
            help="Restore reports from the given backup file.",
        )
        parser.add_argument(
            "--report-ids",
            nargs="+",
            type=int,
            help="Anonymize reports with the given IDs.",
        )
        parser.add_argument(
            "--load_only",
            action="store_true",
            help="Load the author information tables without propagating the changes to the reports.",
        )

    def handle(self, *args, **kwargs):
        if not kwargs["backup_file"]:
            self.stdout.write(
                self.style.ERROR("You must specify a backup file path to restore from.")
            )
            return

        if not os.path.exists(kwargs["backup_file"]):
            self.stdout.write(
                self.style.ERROR(f"Backup file {kwargs['backup_file']} does not exist.")
            )
            return

        results = list(deserialize("json", open(kwargs["backup_file"])))

        ARCs: list[AnonymizedReportContributor] = [
            r.object
            for r in results
            if isinstance(r.object, AnonymizedReportContributor)
        ]

        # If only selected reports are to be restored, filter the ARCs
        if kwargs["report_ids"]:
            ARCs = [arc for arc in ARCs if arc.report.id in kwargs["report_ids"]]

        # If only loading the tables, do not update the reports
        if kwargs["load_only"]:
            updated = AnonymizedReportContributor.objects.bulk_update(
                ARCs,
                ["anonymized_author", "original_author", "invitation_email"],
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded {updated} AnonymizedReportContributors from {kwargs['backup_file']}."
                )
            )

        else:
            reports_to_restore = [arc.report for arc in ARCs]

            # Bulk-update the ARCs before updating the reports
            AnonymizedReportContributor.objects.bulk_update(
                ARCs,
                ["anonymized_author", "original_author", "invitation_email"],
            )

            updated_objects = []
            for report in reports_to_restore:
                updated_objects.append(
                    report.anonymize_author_long_term(commit=False, restore=True)
                )

            # Unpack the updated objects into model-specific lists
            ARCs, reports, invitations = zip(*updated_objects)
            invitations = list(itertools.chain.from_iterable(invitations))

            # Bulk-update the reports, and invitations since commit=False
            Report.objects.bulk_update(reports, ["author"])
            RefereeInvitation.objects.bulk_update(
                invitations,
                ["referee", "email_address"],
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Restored {len(reports_to_restore)} reports "
                    f"and {len(invitations)} refereeing invitations."
                )
            )
