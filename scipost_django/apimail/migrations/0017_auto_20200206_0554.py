# Generated by Django 2.1.8 on 2020-02-06 04:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("apimail", "0016_auto_20200206_0515"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="storedmessageattachmentfilebridge",
            name="attachment_file",
        ),
        migrations.RemoveField(
            model_name="storedmessageattachmentfilebridge",
            name="message",
        ),
        migrations.RenameField(
            model_name="attachmentfile",
            old_name="file_upload",
            new_name="file",
        ),
        migrations.RenameField(
            model_name="composedmessage",
            old_name="attachments",
            new_name="attachment_files",
        ),
        migrations.AddField(
            model_name="storedmessage",
            name="attachment_files",
            field=models.ManyToManyField(blank=True, to="apimail.AttachmentFile"),
        ),
        migrations.DeleteModel(
            name="StoredMessageAttachmentFileBridge",
        ),
    ]
