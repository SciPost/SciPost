# Generated by Django 3.2.16 on 2022-12-15 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0129_alter_submission_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='editorialassignment',
            name='refusal_reason',
            field=models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('VAC', 'Away on vacation'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('CCM', 'Conflict of interest: close competitor'), ('COT', 'Conflict of interest: other'), ('NIR', 'Cannot give an impartial assessment'), ('OFE', 'Outside of my field of expertise'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should desk reject this paper')], max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='editorialassignment',
            name='status',
            field=models.CharField(choices=[('preassigned', 'Preassigned'), ('invited', 'Invited'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('completed', 'Completed'), ('deprecated', 'Deprecated'), ('replaced', 'Replaced')], default='preassigned', max_length=16),
        ),
        migrations.AlterField(
            model_name='refereeinvitation',
            name='refusal_reason',
            field=models.CharField(blank=True, choices=[('BUS', 'Too busy'), ('VAC', 'Away on vacation'), ('COI', 'Conflict of interest: coauthor in last 5 years'), ('CCC', 'Conflict of interest: close colleague'), ('CCM', 'Conflict of interest: close competitor'), ('COT', 'Conflict of interest: other'), ('NIR', 'Cannot give an impartial assessment'), ('OFE', 'Outside of my field of expertise'), ('NIE', 'Not interested enough'), ('DNP', 'SciPost should desk reject this paper')], max_length=3, null=True),
        ),
    ]
