# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-29 13:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("submissions", "0001_initial"),
        ("comments", "0001_initial"),
        ("commentaries", "0002_auto_20171229_1435"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("scipost", "0002_auto_20171229_1435"),
        ("theses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="author",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments",
                to="scipost.Contributor",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="commentary",
            field=models.ForeignKey(
                blank=True,
                help_text="Warning: This field is out of service and will be removed in the future.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="commentaries.Commentary",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="content_type",
            field=models.ForeignKey(
                help_text="Warning: Rather use/edit `content_object` instead or be 100% sure you know what you are doing!",
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.ContentType",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="in_agreement",
            field=models.ManyToManyField(
                blank=True, related_name="in_agreement", to="scipost.Contributor"
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="in_disagreement",
            field=models.ManyToManyField(
                blank=True, related_name="in_disagreement", to="scipost.Contributor"
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="in_notsure",
            field=models.ManyToManyField(
                blank=True, related_name="in_notsure", to="scipost.Contributor"
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="in_reply_to_comment",
            field=models.ForeignKey(
                blank=True,
                help_text="Warning: This field is out of service and will be removed in the future.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="nested_comments_old",
                to="comments.Comment",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="in_reply_to_report",
            field=models.ForeignKey(
                blank=True,
                help_text="Warning: This field is out of service and will be removed in the future.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="submissions.Report",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="submission",
            field=models.ForeignKey(
                blank=True,
                help_text="Warning: This field is out of service and will be removed in the future.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comments_old",
                to="submissions.Submission",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="thesislink",
            field=models.ForeignKey(
                blank=True,
                help_text="Warning: This field is out of service and will be removed in the future.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="theses.ThesisLink",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="vetted_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="comment_vetted_by",
                to="scipost.Contributor",
            ),
        ),
    ]
