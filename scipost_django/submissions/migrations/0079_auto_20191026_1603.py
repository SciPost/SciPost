# Generated by Django 2.1.8 on 2019-10-26 14:03

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0078_auto_20191023_1508"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="editorialdecision",
            options={
                "ordering": ["submission", "taken_on"],
                "verbose_name": "Editorial Decision",
                "verbose_name_plural": "Editorial Decisions",
            },
        ),
    ]
