# Generated by Django 3.2.16 on 2023-01-30 04:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("forums", "0015_auto_20230130_0459"),
    ]

    operations = [
        migrations.AddField(
            model_name="forum",
            name="cf_nr_posts",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
