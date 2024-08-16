# Generated by Django 4.2.10 on 2024-08-15 16:58

import secrets
from django.db import migrations, models
from django.utils import timezone


def reset_profile_email_verification_tokens(apps, schema_editor):
    ProfileEmail = apps.get_model("profiles", "ProfileEmail")
    for email in ProfileEmail.objects.all():
        email.verification_token = secrets.token_urlsafe(40)
        email.verified = email.primary and email.still_valid
        email.save()


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0041_profile_orcid_authenticated"),
    ]

    operations = [
        migrations.AddField(
            model_name="profileemail",
            name="token_expiration",
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AddField(
            model_name="profileemail",
            name="verification_token",
            field=models.CharField(max_length=128, null=True, unique=False),
        ),
        migrations.RunPython(
            reset_profile_email_verification_tokens,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="profileemail",
            name="verification_token",
            field=models.CharField(max_length=128, unique=True, null=False),
        ),
    ]
