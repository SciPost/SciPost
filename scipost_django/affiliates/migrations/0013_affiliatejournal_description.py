# Generated by Django 4.2.10 on 2024-05-23 08:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("affiliates", "0012_affiliatejournal_logo_svg"),
    ]

    operations = [
        migrations.AddField(
            model_name="affiliatejournal",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]