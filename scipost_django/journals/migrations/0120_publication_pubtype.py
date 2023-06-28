# Generated by Django 3.2.14 on 2022-08-19 11:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journals", "0119_alter_publication_pdf_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="pubtype",
            field=models.CharField(
                choices=[
                    ("article", "Article"),
                    ("codebase_release", "Codebase release"),
                ],
                default="article",
                max_length=32,
            ),
        ),
    ]
