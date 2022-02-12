# Generated by Django 3.2.5 on 2022-01-28 11:10

from django.db import migrations


def create_markup_queue(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Queue = apps.get_model("helpdesk", "Queue")

    developers, created = Group.objects.get_or_create(name="Developers")
    markup_queue, created = Queue.objects.get_or_create(
        name="Markup",
        slug="markup",
        description="Markup issues",
        managing_group=developers,
    )
    markup_queue.response_groups.add(developers)


class Migration(migrations.Migration):

    dependencies = [
        ("helpdesk", "0010_auto_20190620_0817"),
    ]

    operations = [
        migrations.RunPython(
            create_markup_queue, reverse_code=migrations.RunPython.noop
        ),
    ]