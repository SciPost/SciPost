# Generated by Django 3.2.17 on 2023-04-03 05:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("title", models.CharField(max_length=64)),
                ("slug", models.SlugField(unique=True)),
                ("description", models.TextField(default="(insert description)")),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["title"],
            },
        ),
        migrations.CreateModel(
            name="BlogPost",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("published", "Published"),
                            ("delisted", "Delisted"),
                        ],
                        max_length=16,
                    ),
                ),
                ("title", models.CharField(max_length=256)),
                ("slug", models.SlugField(unique=True)),
                ("blurb", models.TextField()),
                ("body", models.TextField()),
                ("date_posted", models.DateTimeField()),
                ("categories", models.ManyToManyField(blank=True, to="blog.Category")),
                (
                    "posted_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-date_posted"],
            },
        ),
    ]
