# Generated by Django 4.2.10 on 2024-03-15 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0037_pubfraccompensation_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="pubfrac",
            options={"verbose_name": "PubFrac", "verbose_name_plural": "PubFracs"},
        ),
    ]