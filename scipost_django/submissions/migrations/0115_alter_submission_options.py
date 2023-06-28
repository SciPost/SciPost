# Generated by Django 3.2.16 on 2022-11-22 04:39

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0114_submission_internal_plagiarism_matches"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="submission",
            options={
                "ordering": ["-submission_date"],
                "permissions": [
                    ("take_edadmin_actions", "Take editorial admin actions"),
                    ("view_edadmin_info", "View editorial admin information"),
                ],
            },
        ),
    ]
