# Generated by Django 4.2.10 on 2024-08-05 13:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0134_journal_alternative_journals"),
    ]

    operations = [
        migrations.AlterField(
            model_name="publicationresource",
            name="_type",
            field=models.CharField(
                choices=[
                    ("source_repo", "Publication source files repository"),
                    ("release_repo", "Codebase release version (archive) repository"),
                    ("live_repo", "Live (external) repository"),
                    ("supplemental_info", "Supplemental information"),
                ],
                max_length=32,
            ),
        ),
    ]
