# Generated by Django 3.2.16 on 2022-12-05 04:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0127_auto_20221204_1439"),
    ]

    operations = [
        migrations.RenameField(
            model_name="plagiarismassessment",
            old_name="passed_on",
            new_name="date_set",
        ),
        migrations.AlterField(
            model_name="plagiarismassessment",
            name="comments_for_authors",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="plagiarismassessment",
            name="comments_for_edadmin",
            field=models.TextField(blank=True),
        ),
    ]
