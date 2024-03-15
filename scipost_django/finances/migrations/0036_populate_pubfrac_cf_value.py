# Generated by Django 4.2.10 on 2024-03-15 04:11

from django.db import migrations


def populate_pubfrac_cf_value(apps, schema_editor):
    PubFrac = apps.get_model("finances.PubFrac")
    Journal = apps.get_model("journals.Journal")

    # Some contortions required since model methods not available in migrations
    for pf in PubFrac.objects.all():
        if pf.publication.in_journal:
            journal = Journal.objects.get(pk=pf.publication.in_journal.id)
        elif pf.publication.in_issue.in_journal:
            journal = Journal.objects.get(pk=pf.publication.in_issue.in_journal.id)
        else:
            journal = Journal.objects.get(pk=pf.publication.in_issue.in_volume.in_journal.id)
        cost_per_publication = journal.cost_info[pf.publication.publication_date.year] \
            if pf.publication.publication_date.year in journal.cost_info else \
               journal.cost_info["default"]
        pf.cf_value = int(pf.fraction * cost_per_publication)
        pf.save()


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0035_pubfrac_cf_value"),
    ]

    operations = [
        migrations.RunPython(
            populate_pubfrac_cf_value,
            reverse_code=migrations.RunPython.noop,
        )
    ]
