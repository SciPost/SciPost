# Generated by Django 4.2.10 on 2024-09-02 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("journals", "0135_alter_publicationresource__type"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="author_info_source",
            field=models.TextField(blank=True, null=True),
        ),
    ]