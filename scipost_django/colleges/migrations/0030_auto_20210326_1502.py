# Generated by Django 2.2.16 on 2021-03-26 14:02

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("colleges", "0029_mark_guest_Fellows"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="fellowship",
            name="guest",
        ),
        migrations.RemoveField(
            model_name="potentialfellowship",
            name="elected",
        ),
    ]
