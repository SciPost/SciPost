# Generated by Django 3.2.18 on 2024-02-20 15:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("scipost", "0040_auto_20210310_2026"),
        ("profiles", "0037_enable_unaccent"),
    ]

    operations = [
        migrations.AddField(
            model_name="profileemail",
            name="added_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="profile_emails_added",
                to="scipost.contributor",
            ),
        ),
        migrations.AddField(
            model_name="profileemail",
            name="verified",
            field=models.BooleanField(default=False),
        ),
    ]
