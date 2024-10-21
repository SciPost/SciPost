# Generated by Django 4.2.15 on 2024-10-09 14:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submissions", "0165_add_journal_transfer_conditional_offer"),
    ]

    operations = [
        migrations.AlterField(
            model_name="readiness",
            name="status",
            field=models.CharField(
                choices=[
                    ("perhaps_later", "Perhaps later"),
                    (
                        "could_if_transferred",
                        "I could, if transferred to lower journal",
                    ),
                    ("too_busy", "I would, but I'm currently too busy"),
                    ("conditional", "I would, if transferred"),
                    ("not_interested", "I won't, I'm not interested enough"),
                    ("desk_reject", "I won't, and vote for desk rejection"),
                ],
                max_length=32,
            ),
        ),
    ]