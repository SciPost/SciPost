# Generated by Django 2.2.16 on 2021-05-08 14:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("affiliates", "0002_auto_20210508_1629"),
    ]

    operations = [
        migrations.AlterField(
            model_name="affiliatepublication",
            name="journal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="publications",
                to="affiliates.AffiliateJournal",
            ),
        ),
    ]
