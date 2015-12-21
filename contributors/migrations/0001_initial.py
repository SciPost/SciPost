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
                ('orcid_id', models.CharField(verbose_name='ORCID id', default='', null=True, blank=True, max_length=20)),
                ('affiliation', models.CharField(verbose_name='affiliation', max_length=300)),
                ('address', models.CharField(verbose_name='address', blank=True, max_length=1000)),
                ('personalwebpage', models.URLField(verbose_name='personal web page', blank=True)),
                ('nr_comments', models.PositiveSmallIntegerField(default=0)),
                ('nr_comment_relevance_ratings', models.IntegerField(default=0)),
                ('comment_relevance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_importance_ratings', models.IntegerField(default=0)),
                ('comment_importance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_clarity_ratings', models.IntegerField(default=0)),
                ('comment_clarity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_validity_ratings', models.IntegerField(default=0)),
                ('comment_validity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_comment_rigour_ratings', models.IntegerField(default=0)),
                ('comment_rigour_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_authorreplies', models.PositiveSmallIntegerField(default=0)),
                ('nr_authorreply_relevance_ratings', models.IntegerField(default=0)),
                ('authorreply_relevance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_authorreply_importance_ratings', models.IntegerField(default=0)),
                ('authorreply_importance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_authorreply_clarity_ratings', models.IntegerField(default=0)),
                ('authorreply_clarity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_authorreply_validity_ratings', models.IntegerField(default=0)),
                ('authorreply_validity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_authorreply_rigour_ratings', models.IntegerField(default=0)),
                ('authorreply_rigour_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_reports', models.PositiveSmallIntegerField(default=0)),
                ('nr_report_relevance_ratings', models.IntegerField(default=0)),
                ('report_relevance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_importance_ratings', models.IntegerField(default=0)),
                ('report_importance_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_clarity_ratings', models.IntegerField(default=0)),
                ('report_clarity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_validity_ratings', models.IntegerField(default=0)),
                ('report_validity_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('nr_report_rigour_ratings', models.IntegerField(default=0)),
                ('report_rigour_rating', models.DecimalField(max_digits=3, default=0, decimal_places=0)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
