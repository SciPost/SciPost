# Generated by Django 3.2.14 on 2022-08-19 17:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0120_publication_pubtype'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='publication',
            name='BiBTeX_entry',
        ),
    ]