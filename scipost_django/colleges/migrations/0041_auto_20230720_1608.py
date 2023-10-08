# Generated by Django 3.2.18 on 2023-07-20 14:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("colleges", "0040_auto_20230719_2108"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fellowshipnominationdecision",
            name="voting_round",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="decision",
                to="colleges.fellowshipnominationvotinground",
            ),
        ),
        migrations.AlterField(
            model_name="fellowshipnominationvote",
            name="vote",
            field=models.CharField(
                choices=[
                    ("agree", "Agree"),
                    ("abstain", "Abstain"),
                    ("disagree", "Disagree"),
                    ("veto", "Veto"),
                ],
                max_length=16,
            ),
        ),
    ]
