__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import hashlib
import os
import shutil

from django.core.management import BaseCommand
from django.db.models import Count

from ...models import AttachmentFile


class Command(BaseCommand):
    def handle(self, *args, **options):
        # First, ensure that all files have their hash
        for af in AttachmentFile.objects.filter(sha224_hash__exact=""):
            print(af.file.name)
            hasher = hashlib.sha224()
            for c in af.file.chunks():
                hasher.update(c)
            AttachmentFile.objects.filter(uuid=af.uuid).update(
                sha224_hash=hasher.hexdigest()
            )

        # Then dedupe the files
        duplicate_counts = (
            AttachmentFile.objects.values("sha224_hash")
            .annotate(count=Count("sha224_hash"))
            .filter(count__gt=1)
        )
        print(duplicate_counts)
        nr_files = 0
        size_sum = 0
        for entry in duplicate_counts:
            qs = AttachmentFile.objects.filter(sha224_hash=entry["sha224_hash"])
            anchor = qs.first()
            for dup in qs.exclude(uuid=anchor.uuid):
                # Reset the relations to ComposedMessage and StoredMessage
                for sm in dup.storedmessage_set.all():
                    sm.attachment_files.add(anchor)
                    sm.attachment_files.remove(dup)
                for cm in dup.composedmessage_set.all():
                    cm.attachment_files.add(anchor)
                    cm.attachment_files.remove(dup)
                # Remove the file
                nr_files += 1
                size_sum += dup.file.size
                os.remove(dup.file.path)
                # Clean up the directory structure by removing possibly empty dirs:
                # preserve the first directory with first two letters of uuid,
                # and thus recursively remove the directory with first two pairs of uuid chars
                shutil.rmtree(dup.uuid_01_23_directory_path)

            # Finally, remove the objects except the anchor
            qs.exclude(uuid=anchor.uuid).delete()
            print(
                "cleanup_attachment_files: removed %d files (total size: %d)"
                % (nr_files, size_sum)
            )
