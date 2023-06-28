# Generated by Django 2.1.8 on 2019-10-17 17:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0074_auto_20191017_0949"),
    ]

    operations = [
        migrations.AlterField(
            model_name="alternativerecommendation",
            name="recommendation",
            field=models.SmallIntegerField(
                choices=[
                    (1, "Publish"),
                    (-4, "Reconsult previous referees"),
                    (-5, "Seek additional referees"),
                    (-1, "Ask for minor revision"),
                    (-2, "Ask for major revision"),
                    (-3, "Reject"),
                ]
            ),
        ),
    ]
