# Generated by Django 3.2.16 on 2023-01-29 18:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('forums', '0013_post_absolute_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='anchor_content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='forum_or_meeting_posts', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='post',
            name='anchor_object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]