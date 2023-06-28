# Generated by Django 3.2.16 on 2022-11-29 12:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0125_alter_submission_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="submission",
            name="status",
            field=models.CharField(
                choices=[
                    ("incoming", "Submission incoming, awaiting EdAdmin"),
                    ("admission_failed", "Admission failed"),
                    ("preassignment", "In preassignment"),
                    ("preassignment_failed", "Preassignment failed"),
                    ("seeking_assignment", "Seeking assignment"),
                    (
                        "assignment_failed",
                        "Failed to assign Editor-in-charge; manuscript rejected",
                    ),
                    ("refereeing_in_preparation", "Refereeing in preparation"),
                    ("in_refereeing", "In refereeing"),
                    (
                        "refereeing_closed",
                        "Refereeing closed (awaiting author replies and EdRec)",
                    ),
                    ("awaiting_resubmission", "Awaiting resubmission"),
                    ("resubmitted", "Has been resubmitted"),
                    ("voting_in_preparation", "Voting in preparation"),
                    ("in_voting", "In voting"),
                    ("awaiting_decision", "Awaiting decision"),
                    ("accepted_in_target", "Accepted in target Journal"),
                    (
                        "accepted_alt_puboffer_waiting",
                        "Accepted in alternative Journal; awaiting puboffer acceptance",
                    ),
                    ("accepted_alt", "Accepted in alternative Journal"),
                    ("rejected", "Publication decision taken: reject"),
                    ("withdrawn", "Withdrawn by the Authors"),
                    ("published", "Published"),
                ],
                default="incoming",
                max_length=30,
            ),
        ),
    ]
