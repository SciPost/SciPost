# Generated by Django 4.2.15 on 2024-09-20 09:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0136_publication_author_info_source"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journal",
            name="alternative_journals",
            field=models.ManyToManyField(blank=True, to="journals.journal"),
        ),
    ]
