# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-29 20:25
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('commentaries', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthorshipClaim',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.SmallIntegerField(choices=[(1, 'accepted'), (0, 'not yet vetted (pending)'), (-1, 'rejected')], default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('activation_key', models.CharField(default='', max_length=40)),
                ('key_expires', models.DateTimeField(default=django.utils.timezone.now)),
                ('status', models.SmallIntegerField(choices=[(0, 'newly registered'), (1, 'normal user'), (-1, 'not a professional scientist'), (-2, 'other account already exists'), (-3, 'barred from SciPost'), (-4, 'account disabled')], default=0)),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')], max_length=4)),
                ('discipline', models.CharField(choices=[('physics', 'Physics')], default='physics', max_length=20)),
                ('orcid_id', models.CharField(blank=True, max_length=20, verbose_name='ORCID id')),
                ('country_of_employment', django_countries.fields.CountryField(max_length=2)),
                ('affiliation', models.CharField(max_length=300, verbose_name='affiliation')),
                ('address', models.CharField(blank=True, default='', max_length=1000, verbose_name='address')),
                ('personalwebpage', models.URLField(blank=True, verbose_name='personal web page')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('vetted_by', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor')),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')], max_length=4)),
                ('first_name', models.CharField(default='', max_length=30)),
                ('last_name', models.CharField(default='', max_length=30)),
                ('email_address', models.EmailField(max_length=254)),
                ('invitation_type', models.CharField(choices=[('F', 'Editorial Fellow'), ('C', 'Contributor')], default='C', max_length=2)),
                ('message_style', models.CharField(choices=[('F', 'formal'), ('P', 'personal')], default='F', max_length=1)),
                ('personal_message', models.TextField(blank=True, null=True)),
                ('invitation_key', models.CharField(default='', max_length=40)),
                ('key_expires', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_sent', models.DateTimeField(default=django.utils.timezone.now)),
                ('responded', models.BooleanField(default=False)),
                ('invited_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scipost.Contributor')),
            ],
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='claimant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claimant', to='scipost.Contributor'),
        ),
        migrations.AddField(
            model_name='authorshipclaim',
            name='commentary',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='commentaries.Commentary'),
        ),
    ]
