# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("submissions", "0001_initial"),
        ("journals", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("funders", "0002_auto_20171229_1435"),
        # Deprecation of affiliations app 2019-04-04
        #        ('affiliations', '0002_auto_20171229_1435'),
        ("scipost", "0002_auto_20171229_1435"),
    ]

    operations = [
        migrations.AddField(
            model_name="publication",
            name="accepted_submission",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to="submissions.Submission"
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="authors",
            field=models.ManyToManyField(
                blank=True, related_name="publications", to="scipost.Contributor"
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="authors_claims",
            field=models.ManyToManyField(
                blank=True,
                related_name="claimed_publications",
                to="scipost.Contributor",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="authors_false_claims",
            field=models.ManyToManyField(
                blank=True,
                related_name="false_claimed_publications",
                to="scipost.Contributor",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="authors_unregistered",
            field=models.ManyToManyField(
                blank=True,
                related_name="publications",
                to="journals.UnregisteredAuthor",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="first_author",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="first_author_publications",
                to="scipost.Contributor",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="first_author_unregistered",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="first_author_publications",
                to="journals.UnregisteredAuthor",
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="funders_generic",
            field=models.ManyToManyField(
                blank=True, related_name="publications", to="funders.Funder"
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="grants",
            field=models.ManyToManyField(
                blank=True, related_name="publications", to="funders.Grant"
            ),
        ),
        migrations.AddField(
            model_name="publication",
            name="in_issue",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="journals.Issue"
            ),
        ),
        # Deprecation of affiliations app 2019-04-04
        # migrations.AddField(
        #     model_name='publication',
        #     name='institutions',
        #     field=models.ManyToManyField(blank=True, related_name='publications', to='affiliations.Institution'),
        # ),
        migrations.AddField(
            model_name="issue",
            name="in_volume",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="journals.Volume"
            ),
        ),
        migrations.AddField(
            model_name="genericdoideposit",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AddField(
            model_name="doajdeposit",
            name="publication",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="journals.Publication"
            ),
        ),
        migrations.AddField(
            model_name="deposit",
            name="publication",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="journals.Publication"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="volume",
            unique_together=set([("number", "in_journal")]),
        ),
        migrations.AlterUniqueTogether(
            name="issue",
            unique_together=set([("number", "in_volume")]),
        ),
    ]
