# Generated by Django 2.1.8 on 2020-02-05 07:02

import apimail.validators
from django.db import migrations, models
import django.db.models.deletion
import scipost.storage


class Migration(migrations.Migration):

    dependencies = [
        ('apimail', '0014_auto_20200131_0956'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComposedMessageAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_file', models.FileField(storage=scipost.storage.SecureFileStorage(), upload_to='uploads/mail/composed_messages/attachments/%Y/%m/%d/', validators=[apimail.validators.validate_max_email_attachment_file_size])),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='apimail.ComposedMessage')),
            ],
        ),
    ]