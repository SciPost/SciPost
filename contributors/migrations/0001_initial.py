# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contributor',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('rank', models.SmallIntegerField(default=0, choices=[(0, 'newly registered'), (1, 'normal user'), (2, 'SciPost Commentary Editor'), (3, 'SciPost Journal Editor'), (4, 'SciPost Journal Editor-in-chief'), (5, 'SciPost Lead Editor'), (-1, 'not a professional scientist'), (-2, 'other account already exists'), (-3, 'barred from SciPost'), (-4, 'account disabled')])),
                ('title', models.CharField(max_length=4, choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')])),
                ('orcid_id', models.CharField(blank=True, null=True, max_length=20, default='', verbose_name='ORCID id')),
                ('affiliation', models.CharField(max_length=300, verbose_name='affiliation')),
                ('address', models.CharField(blank=True, max_length=1000, verbose_name='address')),
                ('personalwebpage', models.URLField(blank=True, verbose_name='personal web page')),
                ('nr_reports', models.PositiveSmallIntegerField(default=0)),
                ('report_clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('report_correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('report_usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('nr_comments', models.PositiveSmallIntegerField(default=0)),
                ('comment_clarity_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('comment_correctness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('comment_usefulness_rating', models.DecimalField(decimal_places=0, default=0, max_digits=3)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
