# Generated by Django 2.2.16 on 2021-05-08 14:29

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    dependencies = [
        ('affiliates', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='affiliatejournal',
            name='slug',
            field=models.SlugField(max_length=128, unique=True, validators=[django.core.validators.RegexValidator(re.compile('^[-\\w]+\\Z'), "Enter a valid 'slug' consisting of Unicode letters, numbers, underscores, or hyphens.", 'invalid')]),
        ),
    ]
