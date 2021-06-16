# Generated by Django 2.1.8 on 2019-06-21 05:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0009_auto_20190310_0715'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forum',
            name='description',
            field=models.TextField(blank=True, help_text='You can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.', null=True),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='minutes',
            field=models.TextField(blank=True, help_text='To be filled in after completion of the meeting.\nYou can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.', null=True),
        ),
        migrations.AlterField(
            model_name='meeting',
            name='preamble',
            field=models.TextField(help_text='Explanatory notes for the meeting.\nYou can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.'),
        ),
        migrations.AlterField(
            model_name='post',
            name='text',
            field=models.TextField(help_text='You can use plain text, Markdown or reStructuredText; see our <a href="/markup/help/" target="_blank">markup help</a> pages.'),
        ),
    ]