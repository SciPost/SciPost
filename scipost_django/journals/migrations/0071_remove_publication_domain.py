# Generated by Django 2.1.8 on 2019-09-21 19:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0070_publication_approaches"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="publication",
            name="domain",
        ),
    ]
