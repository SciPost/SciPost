# Generated by Django 4.2.10 on 2024-03-28 11:53

from django.db import migrations, models
import scipost.fields


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0151_report_publicly_visible"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="approaches",
            field=scipost.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[
                        ("theoretical", "Theoretical"),
                        ("experimental", "Experimental"),
                        ("computational", "Computational"),
                        ("phenomenological", "Phenomenological"),
                        ("observational", "Observational"),
                        ("clinical", "Clinical"),
                    ],
                    max_length=24,
                ),
                blank=True,
                null=True,
                size=None,
            ),
        ),
    ]
