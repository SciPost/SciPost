# Generated by Django 2.1.8 on 2020-01-15 20:31

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("apimail", "0005_emailaccount_emailaccountaccess"),
    ]

    operations = [
        migrations.AddField(
            model_name="storedmessage",
            name="read_by",
            field=models.ManyToManyField(
                related_name="_storedmessage_read_by_+", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
