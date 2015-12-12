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
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('rank', models.SmallIntegerField(default=0, choices=[(0, 'newly registered'), (1, 'normal user'), (2, 'SciPost Commentary Editor'), (3, 'SciPost Journal Editor'), (4, 'SciPost Journal Editor-in-chief'), (5, 'SciPost Lead Editor'), (-1, 'not a professional scientist'), (-2, 'other account already exists'), (-3, 'barred from SciPost'), (-4, 'account disabled')])),
                ('title', models.CharField(choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')], max_length=4)),
                ('orcid_id', models.CharField(default='', verbose_name='ORCID id', max_length=20, blank=True, null=True)),
                ('affiliation', models.CharField(verbose_name='affiliation', max_length=300)),
                ('address', models.CharField(verbose_name='address', max_length=1000, blank=True)),
                ('personalwebpage', models.URLField(verbose_name='personal web page', blank=True)),
                ('nr_comments', models.PositiveSmallIntegerField(default=0)),
                ('nr_comment_clarity_ratings', models.IntegerField(default=0)),
                ('comment_clarity_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_comment_validity_ratings', models.IntegerField(default=0)),
                ('comment_validity_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_comment_rigour_ratings', models.IntegerField(default=0)),
                ('comment_rigour_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_comment_originality_ratings', models.IntegerField(default=0)),
                ('comment_originality_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_comment_significance_ratings', models.IntegerField(default=0)),
                ('comment_significance_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_reports', models.PositiveSmallIntegerField(default=0)),
                ('nr_report_clarity_ratings', models.IntegerField(default=0)),
                ('report_clarity_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_report_validity_ratings', models.IntegerField(default=0)),
                ('report_validity_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_report_rigour_ratings', models.IntegerField(default=0)),
                ('report_rigour_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_report_originality_ratings', models.IntegerField(default=0)),
                ('report_originality_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('nr_report_significance_ratings', models.IntegerField(default=0)),
                ('report_significance_rating', models.DecimalField(default=0, decimal_places=0, max_digits=3)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
