# Generated by Django 3.2.18 on 2023-08-25 09:02

from django.db import migrations
from django.contrib.postgres.operations import UnaccentExtension


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0020_rename_grid_json_organization_ror_json"),
    ]

    operations = [
        UnaccentExtension(),
    ]