# Generated by Django 3.2.17 on 2023-04-18 12:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="blogpost",
            name="blurb_image",
            field=models.ImageField(blank=True, upload_to="blog/posts/%Y/%m"),
        ),
    ]
