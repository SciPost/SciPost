# Generated by Django 3.2.16 on 2023-01-17 08:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0133_auto_20230116_1943'),
    ]

    operations = [
        migrations.RenameField(
            model_name='qualification',
            old_name='status',
            new_name='expertise_level',
        ),
    ]