# Generated by Django 2.1.8 on 2019-11-13 21:26

import apimail.validators
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import scipost.storage


class Migration(migrations.Migration):
    dependencies = [
        ("apimail", "0002_auto_20191113_1547"),
    ]

    operations = [
        migrations.CreateModel(
            name="StoredMessageAttachment",
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
                    "_file",
                    models.FileField(
                        storage=scipost.storage.SecureFileStorage(),
                        upload_to="uploads/mail/stored_messages/attachments/%Y/%m/%d/",
                        validators=[
                            apimail.validators.validate_max_email_attachment_file_size
                        ],
                    ),
                ),
            ],
        ),
        migrations.AlterModelOptions(
            name="storedmessage",
            options={"ordering": ["-data__Date"]},
        ),
        migrations.AddField(
            model_name="storedmessageattachment",
            name="message",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attachments",
                to="apimail.StoredMessage",
            ),
        ),
    ]
