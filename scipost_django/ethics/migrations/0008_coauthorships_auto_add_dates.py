from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ethics", "0007_coauthorships_from_cois"),
    ]

    operations = [
        migrations.AlterField(
            model_name="coauthorship",
            name="created",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="coauthorship",
            name="modified",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="coauthoredwork",
            name="date_fetched",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddConstraint(
            model_name="coauthorship",
            constraint=models.CheckConstraint(
                condition=models.Q(("profile_id__lt", models.F("coauthor_id"))),
                name="enforce_profile_ordering",
                violation_error_message="Profile/Coauthor IDs must be in the correct order to avoid duplicates.",
            ),
        ),
        migrations.AddConstraint(
            model_name="coauthorship",
            constraint=models.UniqueConstraint(
                fields=("profile", "coauthor", "work"),
                name="unique_together_profile_coauthor_work",
                violation_error_message="This coauthorship already exists.",
            ),
        ),
    ]
