# Generated by Django 2.2.11 on 2020-07-19 15:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('preprints', '0010_merge_20181207_1008'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='preprint',
            name='scipost_preprint_identifier',
        ),
    ]