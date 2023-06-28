# Generated by Django 3.2.16 on 2023-01-18 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0035_alter_profile_title"),
        ("organizations", "0019_auto_20220314_0723"),
        ("submissions", "0134_rename_status_qualification_expertise_level"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubmissionAuthorProfile",
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
                ("order", models.PositiveSmallIntegerField()),
                (
                    "affiliations",
                    models.ManyToManyField(blank=True, to="organizations.Organization"),
                ),
                (
                    "profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="profiles.profile",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="author_profiles",
                        to="submissions.submission",
                    ),
                ),
            ],
            options={
                "ordering": ("submission", "order"),
            },
        ),
    ]
