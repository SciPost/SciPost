# Generated by Django 5.0.12 on 2025-02-25 08:49

import django.core.validators
from django.db import migrations, models


def blank_to_null(apps, schema_editor):
    Profile = apps.get_model("profiles", "Profile")
    Profile.objects.filter(orcid_id="").update(orcid_id=None)


def null_to_blank(apps, schema_editor):
    Profile = apps.get_model("profiles", "Profile")
    Profile.objects.filter(orcid_id=None).update(orcid_id="")


class Migration(migrations.Migration):
    dependencies = [
        ("ontology", "0009_populate_specialty_topics"),
        ("profiles", "0043_alter_profile_first_name_original_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="orcid_id",
            field=models.CharField(
                blank=True,
                max_length=20,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$",
                        "Please follow the ORCID format, e.g.: 0000-0001-2345-6789",
                    )
                ],
                verbose_name="ORCID id",
            ),
        ),
        migrations.RunPython(blank_to_null, null_to_blank),
        migrations.AddConstraint(
            model_name="profile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("orcid_id__isnull", False)),
                fields=("orcid_id",),
                name="unique_orcid_id",
                violation_error_message="ORCID id must be unique across all profiles.",
            ),
        ),
        migrations.AddConstraint(
            model_name="profile",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("orcid_id__isnull", True),
                    (
                        "orcid_id__regex",
                        "^[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]{1}$",
                    ),
                    _connector="OR",
                ),
                name="orcid_id_format",
                violation_error_message="ORCID id must be of the form 'XXXX-XXXX-XXXX-XXXY', where X is a digit and Y is a digit or 'X'.",
            ),
        ),
    ]
