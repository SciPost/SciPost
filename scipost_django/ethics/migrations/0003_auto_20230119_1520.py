# Generated by Django 3.2.16 on 2023-01-19 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ethics', '0002_submissionclearance'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='submissionclearance',
            options={'ordering': ['submission', 'profile']},
        ),
        migrations.AddConstraint(
            model_name='submissionclearance',
            constraint=models.UniqueConstraint(fields=('profile', 'submission'), name='unique_together_profile_submission'),
        ),
    ]