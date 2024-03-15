# Generated by Django 4.2.10 on 2024-03-15 15:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "scipost",
            "0041_alter_remark_contributor_alter_remark_recommendation_and_more",
        ),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="Note",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                (
                    "visibility",
                    models.CharField(
                        choices=[
                            ("self", "Private"),
                            ("internal", "Internal"),
                            ("public", "Public"),
                        ],
                        default="self",
                        max_length=10,
                    ),
                ),
                (
                    "regarding_object_id",
                    models.PositiveIntegerField(blank=True, null=True),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("modified", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="scipost.contributor",
                    ),
                ),
                (
                    "regarding_content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "ordering": ("-created",),
                "default_related_name": "notes",
            },
        ),
        migrations.CreateModel(
            name="Pin",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("due_date", models.DateField(blank=True, null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "note",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="pins.note"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
