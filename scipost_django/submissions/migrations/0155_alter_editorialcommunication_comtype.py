# Generated by Django 4.2.10 on 2024-08-05 11:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0154_alter_report_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="editorialcommunication",
            name="comtype",
            field=models.CharField(
                choices=[
                    ("EtoA", "Editor-in-charge to Author"),
                    ("EtoR", "Editor-in-charge to Referee"),
                    ("EtoS", "Editor-in-charge to SciPost Editorial Administration"),
                    ("AtoE", "Author to Editor-in-charge"),
                    ("AtoR", "Author to Referee"),
                    ("AtoS", "Author to SciPost Editorial Administration"),
                    ("RtoE", "Referee to Editor-in-charge"),
                    ("RtoA", "Referee to Author"),
                    ("RtoS", "Referee to SciPost Editorial Administration"),
                    ("StoE", "SciPost Editorial Administration to Editor-in-charge"),
                    ("StoA", "SciPost Editorial Administration to Author"),
                    ("StoR", "SciPost Editorial Administration to Referee"),
                ],
                max_length=4,
            ),
        ),
    ]
