# Generated by Django 2.1.8 on 2020-02-06 04:15

import apimail.validators
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import scipost.storage
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("apimail", "0015_composedmessageattachment"),
    ]

    operations = [
        migrations.CreateModel(
            name="AttachmentFile",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "file_upload",
                    models.FileField(
                        storage=scipost.storage.SecureFileStorage(),
                        upload_to="uploads/mail/attachments/%Y/%m/%d/",
                        validators=[
                            apimail.validators.validate_max_email_attachment_file_size
                        ],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StoredMessageAttachmentFileBridge",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("data", django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                (
                    "attachment_file",
                    models.ManyToManyField(to="apimail.AttachmentFile"),
                ),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="apimail.StoredMessage",
                    ),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="composedmessageattachment",
            name="message",
        ),
        migrations.RemoveField(
            model_name="storedmessageattachment",
            name="message",
        ),
        migrations.DeleteModel(
            name="ComposedMessageAttachment",
        ),
        migrations.DeleteModel(
            name="StoredMessageAttachment",
        ),
        migrations.AddField(
            model_name="composedmessage",
            name="attachments",
            field=models.ManyToManyField(blank=True, to="apimail.AttachmentFile"),
        ),
    ]
