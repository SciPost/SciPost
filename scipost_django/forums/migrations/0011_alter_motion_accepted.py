# Generated by Django 3.2.5 on 2021-07-16 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0010_auto_20190621_0701'),
    ]

    operations = [
        migrations.AlterField(
            model_name='motion',
            name='accepted',
            field=models.BooleanField(null=True),
        ),
    ]
