# Generated by Django 2.0.13 on 2019-05-18 09:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0055_auto_20190511_1141"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="needs_conflicts_update",
            field=models.BooleanField(default=True),
        ),
    ]
