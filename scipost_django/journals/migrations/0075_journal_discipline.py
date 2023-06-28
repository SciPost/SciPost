# Generated by Django 2.1.8 on 2019-09-23 09:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0074_journal_style"),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="discipline",
            field=models.CharField(
                choices=[
                    ("physics", "Physics"),
                    ("astrophysics", "Astrophysics"),
                    ("chemistry", "Chemistry"),
                    ("mathematics", "Mathematics"),
                    ("computerscience", "Computer Science"),
                ],
                default="physics",
                max_length=20,
            ),
        ),
    ]
