# Generated by Django 3.2.12 on 2022-03-05 13:46

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("colleges", "0033_fellowshipnominationcomment"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="fellowshipnominationvotinground",
            options={
                "ordering": ["nomination__profile__last_name", "-voting_deadline"],
                "verbose_name_plural": "Fellowship Nomination Voting Rounds",
            },
        ),
    ]
