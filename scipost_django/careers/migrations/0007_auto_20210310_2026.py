# Generated by Django 2.2.16 on 2021-03-10 19:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("careers", "0006_jobapplication_last_udpated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobapplication",
            name="title",
            field=models.CharField(
                choices=[
                    ("PR", "Prof."),
                    ("DR", "Dr"),
                    ("MR", "Mr"),
                    ("MRS", "Mrs"),
                    ("MS", "Ms"),
                    ("MX", "Mx"),
                ],
                max_length=4,
            ),
        ),
    ]
