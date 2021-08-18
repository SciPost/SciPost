# Generated by Django 3.2.5 on 2021-07-16 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apimail', '0031_storedmessage_mime'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addressvalidation',
            name='data',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='attachmentfile',
            name='data',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='composedmessage',
            name='headers_added',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='composedmessageapiresponse',
            name='json',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='event',
            name='data',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='storedmessage',
            name='data',
            field=models.JSONField(default=dict),
        ),
    ]