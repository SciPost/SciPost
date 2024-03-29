# Generated by Django 3.2.12 on 2022-03-09 06:35

from django.db import migrations


def add_events(apps, schema_editor):
    FellowshipNomination = apps.get_model("colleges", "FellowshipNomination")
    FellowshipNominationEvent = apps.get_model("colleges", "FellowshipNominationEvent")

    for n in FellowshipNomination.objects.exclude(events__description="Nominated"):
        event = FellowshipNominationEvent(
            nomination=n,
            description="Nominated",
            on=n.nominated_on,
            by=n.nominated_by,
        )
        event.save()


class Migration(migrations.Migration):
    dependencies = [
        ("colleges", "0038_fellowshipnominationevent"),
    ]

    operations = [
        migrations.RunPython(add_events, reverse_code=migrations.RunPython.noop),
    ]
