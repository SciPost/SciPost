# Generated by Django 4.2.10 on 2024-03-12 10:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("finances", "0028_alter_subsidy_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="subsidyattachment",
            name="git_url",
            field=models.URLField(
                blank=True, help_text="URL to the file's location in GitLab"
            ),
        ),
        migrations.AlterField(
            model_name="subsidyattachment",
            name="subsidy",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attachments",
                to="finances.subsidy",
            ),
        )
    ]
