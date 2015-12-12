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
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('rank', models.SmallIntegerField(choices=[(0, 'newly registered'), (1, 'normal user'), (2, 'SciPost Commentary Editor'), (3, 'SciPost Journal Editor'), (4, 'SciPost Journal Editor-in-chief'), (5, 'SciPost Lead Editor'), (-1, 'not a professional scientist'), (-2, 'other account already exists'), (-3, 'barred from SciPost'), (-4, 'account disabled')], default=0)),
                ('title', models.CharField(max_length=4, choices=[('PR', 'Prof.'), ('DR', 'Dr'), ('MR', 'Mr'), ('MRS', 'Mrs')])),
                ('orcid_id', models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='ORCID id')),
                ('affiliation', models.CharField(max_length=300, verbose_name='affiliation')),
                ('address', models.CharField(max_length=1000, verbose_name='address', blank=True)),
                ('personalwebpage', models.URLField(verbose_name='personal web page', blank=True)),
                ('nr_report_clarity_ratings', models.IntegerField(default=0)),
                ('report_clarity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_validity_ratings', models.IntegerField(default=0)),
                ('report_validity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_rigour_ratings', models.IntegerField(default=0)),
                ('report_rigour_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_originality_ratings', models.IntegerField(default=0)),
                ('report_originality_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_significance_ratings', models.IntegerField(default=0)),
                ('report_significance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_clarity_ratings', models.IntegerField(default=0)),
                ('comment_clarity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_validity_ratings', models.IntegerField(default=0)),
                ('comment_validity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_rigour_ratings', models.IntegerField(default=0)),
                ('comment_rigour_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_originality_ratings', models.IntegerField(default=0)),
                ('comment_originality_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_significance_ratings', models.IntegerField(default=0)),
                ('comment_significance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
