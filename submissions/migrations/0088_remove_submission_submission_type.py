# Generated by Django 2.2.11 on 2020-07-21 04:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0087_remove_submission_arxiv_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='submission_type',
        ),
    ]
