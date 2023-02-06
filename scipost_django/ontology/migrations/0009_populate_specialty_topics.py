# Generated by Django 3.2.16 on 2023-01-22 13:55

from django.db import migrations


def populate_specialty_topics(apps, schema_editor):
    Topic = apps.get_model("ontology.Topic")
    Publication = apps.get_model("journals.Publication")
    Submission = apps.get_model("submissions.Submission")

    # Add topics to specialties, using Publication and Submission info
    for pub in Publication.objects.all():
        for specialty in pub.specialties.all():
            specialty.topics.add(*pub.topics.all())
    for sub in Submission.objects.all():
        for specialty in sub.specialties.all():
            specialty.topics.add(*sub.topics.all())


class Migration(migrations.Migration):

    dependencies = [
        ('ontology', '0008_specialty_topics'),
    ]

    operations = [
        migrations.RunPython(
            populate_specialty_topics,
            reverse_code=migrations.RunPython.noop,
        )
    ]
