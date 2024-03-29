# Generated by Django 3.2.18 on 2023-07-06 14:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("production", "0007_auto_20230706_1502"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productionstream",
            name="status",
            field=models.CharField(
                choices=[
                    ("initiated", "New Stream started"),
                    ("source_requested", "Source files requested"),
                    ("tasked", "Supervisor tasked officer with proofs production"),
                    ("produced", "Proofs have been produced"),
                    ("checked", "Proofs have been checked by Supervisor"),
                    ("sent", "Proofs sent to Authors"),
                    ("returned", "Proofs returned by Authors"),
                    ("corrected", "Corrections implemented"),
                    ("accepted", "Authors have accepted proofs"),
                    ("published", "Paper has been published"),
                    ("cited", "Cited people have been notified/invited to SciPost"),
                    ("completed", "Completed"),
                ],
                default="initiated",
                max_length=32,
            ),
        ),
    ]
