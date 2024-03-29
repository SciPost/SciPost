# Generated by Django 2.1.8 on 2020-01-26 15:09

from django.conf import settings
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("apimail", "0011_auto_20200118_0843"),
    ]

    operations = [
        migrations.CreateModel(
            name="ComposedMessage",
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
                (
                    "uuid",
                    models.UUIDField(db_index=True, default=uuid.uuid4, editable=False),
                ),
                ("created_on", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("ready", "Ready for sending"),
                            ("rendered", "Rendered"),
                            ("sent", "Sent"),
                        ],
                        default="draft",
                        max_length=8,
                    ),
                ),
                ("to_recipient", models.EmailField(max_length=254)),
                (
                    "cc_recipients",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.EmailField(max_length=254),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "bcc_recipients",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.EmailField(max_length=254),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                ("subject", models.CharField(max_length=256)),
                ("body_text", models.TextField()),
                ("body_html", models.TextField(blank=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "from_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="apimail.EmailAccount",
                    ),
                ),
            ],
        ),
    ]
