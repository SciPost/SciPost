# Generated by Django 2.1.8 on 2019-11-14 20:15

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("apimail", "0003_auto_20191113_2226"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="event",
            options={"ordering": ["-data__timestamp"]},
        ),
        migrations.AlterModelOptions(
            name="storedmessage",
            options={"ordering": ["-datetimestamp"]},
        ),
        migrations.AddField(
            model_name="storedmessage",
            name="datetimestamp",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
