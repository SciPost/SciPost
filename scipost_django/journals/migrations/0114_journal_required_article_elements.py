# Generated by Django 3.2.5 on 2021-08-19 13:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0113_submissiontemplate_instructions"),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="required_article_elements",
            field=models.TextField(default="[To be filled in; you can use markup]"),
        ),
    ]
