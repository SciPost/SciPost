# Generated by Django 4.2.15 on 2024-10-07 13:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("series", "0009_collection_event_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
    ]