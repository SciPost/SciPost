# Generated by Django 2.2.11 on 2020-09-15 11:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("submissions", "0092_auto_20200721_1646"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="submission",
            options={"ordering": ["-submission_date"]},
        ),
    ]
