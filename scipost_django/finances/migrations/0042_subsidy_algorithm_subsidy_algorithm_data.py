# Generated by Django 4.2.10 on 2024-03-16 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finances", "0041_remove_publicationexpenditurecoverage_publication_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="subsidy",
            name="algorithm",
            field=models.CharField(
                choices=[
                    ("any_aff", "Any PubFrac with affiliation to org"),
                    (
                        "any_ctry",
                        "Any PubFrac with an affiliation in given list of countries",
                    ),
                    (
                        "any_orgs",
                        "Any PubFrac with an affiliation in given list of orgs",
                    ),
                    (
                        "any_spec",
                        "Any PubFrac of publication in given list of specialties",
                    ),
                    (
                        "all_aff",
                        "All PubFracs of publication with at least one author with affiliation to org",
                    ),
                    (
                        "all_ctry",
                        "All PubFracs of publications having at least one affiliation in given list of countries",
                    ),
                    (
                        "all_orgs",
                        "All PubFracs of publications having at least one affiliation in given list of orgs",
                    ),
                    (
                        "all_spec",
                        "All PubFracs of publication in given list of specialties",
                    ),
                    (
                        "all_fund",
                        "All PubFracs of publication acknowledging org in Funders",
                    ),
                    ("reserves", "Allocate to reserves fund"),
                ],
                default="reserves",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="subsidy",
            name="algorithm_data",
            field=models.JSONField(default=dict),
        ),
    ]
