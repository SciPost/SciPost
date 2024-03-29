# Generated by Django 3.2.5 on 2022-01-29 07:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "colleges",
            "0031_fellowshipinvitation_fellowshipnomination_fellowshipnominationdecision_fellowshipnominationevent_fel",
        ),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="fellowshipnominationevent",
            options={
                "ordering": ["-on"],
                "verbose_name_plural": "Fellowhip Nomination Events",
            },
        ),
        migrations.AddField(
            model_name="fellowshipinvitation",
            name="comments",
            field=models.TextField(
                blank=True,
                help_text='You can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.',
            ),
        ),
        migrations.AddField(
            model_name="fellowshipnomination",
            name="nominator_comments",
            field=models.TextField(
                blank=True,
                help_text='You can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.',
            ),
        ),
        migrations.AddField(
            model_name="fellowshipnominationdecision",
            name="comments",
            field=models.TextField(
                blank=True,
                help_text='You can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.',
            ),
        ),
        migrations.AlterField(
            model_name="fellowshipnominationvote",
            name="comments",
            field=models.TextField(
                blank=True,
                help_text='You can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.',
            ),
        ),
    ]
