# Generated by Django 3.2.5 on 2021-09-13 14:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("proceedings", "0009_auto_20210422_0833"),
        ("submissions", "0108_auto_20210716_0937"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="proceedings",
            field=models.ForeignKey(
                blank=True,
                help_text="Don't find the Proceedings you are looking for? Ask the conference organizers to contact our admin to set things up.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submissions",
                to="proceedings.proceedings",
            ),
        ),
    ]
