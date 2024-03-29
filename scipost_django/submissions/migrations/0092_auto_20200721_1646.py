# Generated by Django 2.2.11 on 2020-07-21 14:46

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0091_remove_submission__is_resubmission"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="submission_date",
            field=models.DateTimeField(
                default=django.utils.timezone.now, verbose_name="submission date"
            ),
        ),
    ]
