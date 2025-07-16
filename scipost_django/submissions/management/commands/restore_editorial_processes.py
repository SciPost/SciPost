import os
from pathlib import Path
from django.core.management import BaseCommand
from django.core.serializers import deserialize
from django.db.models import Model

from anonymization.models import ContributorAnonymization, ProfileAnonymization
from mails.models import MailLog
from submissions.models.communication import EditorialCommunication
from submissions.models.referee_invitation import RefereeInvitation
from submissions.models.submission import SubmissionEvent


class Command(BaseCommand):
    help = (
        "This command temporarily restores a submission thread's editorial processes "
        "by loading the anonymized data from a serialized dump file via the --restore option. "
        "It can also clean out the loaded objects after use via the --clean option. "
        "A file path or hash can be provided to specify which thread to restore. "
        "If a hash is provided, it will try to load "
        "$BACKUP_DIR/anonymized/editorial_processes/anonymized_editorial_processes__{{hash}}.json, "
        "unless a file path is provided which will take precedence."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--thread_hash",
            type=str,
            help="Affect only submissions with the given thread hash.",
        )
        parser.add_argument(
            "--restore",
            action="store_true",
            help="Restore the editorial processes from the dump file.",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean out the loaded objects after use.",
        )
        parser.add_argument(
            "--file_path",
            type=str,
            help="A file path to a dump file to restore from. "
            "If not provided, it will try to load the file from the backup directory.",
        )

    def handle(self, *args, **options):
        DUMP_FILENAME_TEMPLATE = "anonymized_editorial_processes_{hash}.json"
        BACKUPS_DIR = Path(os.environ.get("BACKUP_DIR", "."))
        ANON_BACKUPS_DIR = BACKUPS_DIR / "anonymized" / "editorial_processes"

        if not options.get("restore") and not options.get("clean"):
            raise ValueError("You must specify either --restore or --clean.")

        thread_hash = options.get("thread_hash")
        if not thread_hash:
            raise ValueError("You must provide a thread hash with --thread_hash.")

        default_filename = ANON_BACKUPS_DIR / DUMP_FILENAME_TEMPLATE.format(
            hash=thread_hash
        )
        filename = options.get("file_path") or default_filename

        if options.get("restore") and not os.path.exists(filename):
            raise FileNotFoundError(
                f"The specified file does not exist: {filename}. "
                "Please provide a valid file path or ensure the file exists in the backup directory."
            )

        try:
            with open(filename, "r") as file:
                data = file.read()
                objects = [o.object for o in deserialize("json", data)]
        except Exception as e:
            raise ValueError(
                f"Failed to load objects related to "
                f"editorial processes of thread {thread_hash}: {e}"
            )

        if options.get("restore"):
            self.restore_editorial_processes(objects)
        elif options.get("clean"):
            self.clean_editorial_processes(objects)

    def restore_editorial_processes(self, objects: list[Model]):
        for obj in objects:
            manager = obj.__class__.objects
            if manager.filter(pk=obj.pk).exists():
                # If the object already exists, we update it
                loaded_field_values = {
                    field.name: getattr(obj, field.name)
                    for field in obj._meta.fields
                    if field.name != "id"
                }
                manager.filter(pk=obj.pk).update(**loaded_field_values)
            else:
                # Otherwise, we create a new instance
                obj.save()

    def clean_editorial_processes(self, objects: list[Model]):
        for obj in objects:
            manager = obj.__class__.objects
            if isinstance(obj, (ContributorAnonymization, ProfileAnonymization)):
                # Simply removing the original is enough
                manager.filter(pk=obj.pk).update(original=None)
            elif isinstance(obj, RefereeInvitation):
                manager.filter(pk=obj.pk).update(email_address="")
            elif isinstance(obj, (SubmissionEvent, EditorialCommunication, MailLog)):
                manager.filter(pk=obj.pk).delete()
            else:
                raise TypeError(f"Unsupported object type for cleaning: {type(obj)}")
