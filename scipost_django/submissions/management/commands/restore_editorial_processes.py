from itertools import groupby
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

    @staticmethod
    def model_compare(model: Model) -> str:
        cls_meta = model.__class__._meta
        return cls_meta.object_name + ":" + cls_meta.db_table

    def restore_editorial_processes(self, objects: list[Model]):
        objects.sort(key=Command.model_compare)
        for model, objs in groupby(objects, lambda o: o.__class__):
            existing_pks = list(model.objects.values_list("pk", flat=True))

            to_update: list[Model] = []
            to_create: list[Model] = []
            for obj in objs:
                if obj.pk in existing_pks:
                    to_update.append(obj)
                else:
                    to_create.append(obj)

            model.objects.bulk_create(to_create)
            model.objects.bulk_update(
                to_update,
                [field.name for field in model._meta.fields if not field.primary_key],
            )

    def clean_editorial_processes(self, objects: list[Model]):
        objects.sort(key=Command.model_compare)
        for model, objs in groupby(objects, lambda o: o.__class__):
            obj_pks = [obj.pk for obj in objs]
            if model in (ContributorAnonymization, ProfileAnonymization):
                # Simply removing the original is enough
                model.objects.filter(pk__in=obj_pks).update(original=None)
            elif model in (RefereeInvitation,):
                model.objects.filter(pk__in=obj_pks).update(email_address="")
            elif model in (SubmissionEvent, EditorialCommunication, MailLog):
                model.objects.filter(pk__in=obj_pks).delete()
            else:
                raise TypeError(f"Unsupported object type for cleaning: {type(obj)}")
