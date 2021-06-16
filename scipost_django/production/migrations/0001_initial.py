# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import production.models
import scipost.storage


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductionEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.CharField(choices=[('assignment', 'Assignment'), ('status', 'Status change'), ('message', 'Message'), ('registration', 'Hour registration')], default='message', max_length=64)),
                ('comments', models.TextField(blank=True, null=True)),
                ('noted_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('duration', models.DurationField(blank=True, null=True)),
            ],
            options={
                'ordering': ['noted_on'],
            },
        ),
        migrations.CreateModel(
            name='ProductionEventAttachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment', models.FileField(storage=scipost.storage.SecureFileStorage(), upload_to=production.models.production_event_upload_location)),
            ],
        ),
        migrations.CreateModel(
            name='ProductionStream',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('opened', models.DateTimeField(auto_now_add=True)),
                ('closed', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.CharField(choices=[('initiated', 'New Stream started'), ('tasked', 'Supervisor tasked officer with proofs production'), ('produced', 'Proofs have been produced'), ('checked', 'Proofs have been checked by Supervisor'), ('sent', 'Proofs sent to Authors'), ('returned', 'Proofs returned by Authors'), ('corrected', 'Corrections implemented'), ('accepted', 'Authors have accepted proofs'), ('published', 'Paper has been published'), ('cited', 'Cited people have been notified/invited to SciPost'), ('completed', 'Completed')], default='initiated', max_length=32)),
            ],
            options={
                'permissions': (('can_work_for_stream', 'Can work for stream'), ('can_perform_supervisory_actions', 'Can perform supervisory actions')),
            },
        ),
        migrations.CreateModel(
            name='ProductionUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='production_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Proofs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment', models.FileField(storage=scipost.storage.SecureFileStorage(), upload_to=production.models.proofs_upload_location)),
                ('version', models.PositiveSmallIntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('uploaded', 'Proofs uploaded'), ('sent', 'Proofs sent to authors'), ('accepted_sup', 'Proofs accepted by supervisor'), ('declined_sup', 'Proofs declined by supervisor'), ('accepted', 'Proofs accepted by authors'), ('declined', 'Proofs declined by authors'), ('renewed', 'Proofs renewed')], default='uploaded', max_length=16)),
                ('accessible_for_authors', models.BooleanField(default=False)),
                ('stream', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='proofs', to='production.ProductionStream')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='production.ProductionUser')),
            ],
            options={
                'ordering': ['stream', 'version'],
                'verbose_name_plural': 'Proofs',
            },
        ),
        migrations.AddField(
            model_name='productionstream',
            name='invitations_officer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invitations_officer_streams', to='production.ProductionUser'),
        ),
        migrations.AddField(
            model_name='productionstream',
            name='officer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='streams', to='production.ProductionUser'),
        ),
    ]