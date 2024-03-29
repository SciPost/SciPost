# Generated by Django 2.1.8 on 2019-09-21 17:17

from django.db import migrations, models
import scipost.fields


def domains_to_approaches(apps, schema_editor):
    Publication = apps.get_model("journals.Publication")

    for publication in Publication.objects.filter(domain__contains="E"):
        if publication.approaches:
            publication.approaches.append("experimental")
        else:
            publication.approaches = ("experimental",)
        publication.save()
    for publication in Publication.objects.filter(domain__contains="T"):
        if publication.approaches:
            publication.approaches.append("theoretical")
        else:
            publication.approaches = ("theoretical",)
        publication.save()
    for publication in Publication.objects.filter(domain__contains="C"):
        if publication.approaches:
            publication.approaches.append("computational")
        else:
            publication.approaches = ("computational",)
        publication.save()


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0069_auto_20190911_0547"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
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
