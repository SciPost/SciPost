# Generated by Django 4.2.10 on 2024-04-26 12:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("mailing_lists", "0003_mailinglist"),
    ]

    operations = [
        migrations.CreateModel(
            name="Newsletter",
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
                ("title", models.CharField(max_length=255)),
                ("content", models.TextField()),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("sent_on", models.DateTimeField(blank=True, null=True)),
                ("scheduled_for", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("scheduled", "Scheduled"),
                            ("sent", "Sent"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                (
                    "mailing_list",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="newsletters",
                        to="mailing_lists.mailinglist",
                    ),
                ),
            ],
        ),
    ]
