# Generated by Django 2.2.16 on 2020-09-27 05:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("commentaries", "0018_auto_20200926_2200"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="commentary",
            name="discipline",
        ),
        migrations.RemoveField(
            model_name="commentary",
            name="subject_area",
        ),
    ]
