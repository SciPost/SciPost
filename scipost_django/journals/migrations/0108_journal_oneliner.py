# Generated by Django 2.2.16 on 2021-05-01 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journals', '0107_journal_template_docx'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='oneliner',
            field=models.TextField(blank=True, help_text='One-line description, for Journal card. You can use markup'),
        ),
    ]