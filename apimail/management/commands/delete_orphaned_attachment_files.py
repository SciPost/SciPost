__copyright__ = "Copyright © Stichting SciPost (SciPost Foundation)"
__license__ = "AGPL v3"


import os

from django.core.management import BaseCommand

from ...models import AttachmentFile, ComposedMessage, StoredMessage


class Command(BaseCommand):

    def handle(self, *args, **options):
        uuids_in_cm = [att.uuid for cm in ComposedMessage.objects.all()
                       for att in cm.attachment_files.all()]
        uuids_in_sm = [att.uuid for sm in StoredMessage.objects.all()
                       for att in sm.attachment_files.all()]

        uuids_in_use = set(uuids_in_cm + uuids_in_sm)
        print(uuids_in_use)

        orphaned_att = AttachmentFile.objects.exclude(uuid__in=uuids_in_use)

        print(orphaned_att)

        for orphan_att in orphaned_att:
            # We double-check that we're not deleting any used attachment
            # since the 'exclude' logic above is risky
            # (any mistake in uuids_in_use would lead to unwanted deletion)
            try:
                ComposedMessage.objects.filter(attachment_files__uuid=orphan_att.uuid).first()
            except ComposedMessage.DoesNotExist:
                try:
                    StoredMessage.objects.filter(attachment_files__uuid=orphan_att.uuid).first()
                except StoredMessage.DoesNotExist:
                    print('Deleting %s' % orphan_att.uuid)
                    if orphan_att.file:
                        if os.path.isfile(orphan_att.file.path):
                            os.remove(orphan_att.file.path)
                    orphan_att.delete()
