# Generated by Django 2.2.16 on 2020-10-26 20:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0102_auto_20200930_0602"),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="submission_insert",
            field=models.TextField(
                blank=True, default="[Optional; you can use markup]", null=True
            ),
        ),
    ]
