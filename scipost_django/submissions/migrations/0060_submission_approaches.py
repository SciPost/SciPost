# Generated by Django 2.1.8 on 2019-09-21 17:17

from django.db import migrations, models
import scipost.fields


def domains_to_approaches(apps, schema_editor):
    Submission = apps.get_model("submissions.Submission")

    for submission in Submission.objects.filter(domain__contains="E"):
        if submission.approaches:
            submission.approaches.append("experimental")
        else:
            submission.approaches = ("experimental",)
        submission.save()
    for submission in Submission.objects.filter(domain__contains="T"):
        if submission.approaches:
            submission.approaches.append("theoretical")
        else:
            submission.approaches = ("theoretical",)
        submission.save()
    for submission in Submission.objects.filter(domain__contains="C"):
        if submission.approaches:
            submission.approaches.append("computational")
        else:
            submission.approaches = ("computational",)
        submission.save()


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0059_auto_20190912_0906"),
    ]

    operations = [
        migrations.AddField(
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
                verbose_name="approach(es) [optional]",
            ),
        ),
        migrations.RunPython(
            domains_to_approaches, reverse_code=migrations.RunPython.noop
        ),
    ]
