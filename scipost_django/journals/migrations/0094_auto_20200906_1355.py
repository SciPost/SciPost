# Generated by Django 2.2.11 on 2020-09-06 11:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0093_journal_college"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journal",
            name="college",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="journals",
                to="colleges.College",
            ),
        ),
    ]
