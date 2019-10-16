# Generated by Django 2.1.8 on 2019-10-16 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0072_populate_tiering'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alternativerecommendation',
            name='recommendation',
            field=models.SmallIntegerField(choices=[(1, 'Publish'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')]),
        ),
        migrations.AlterField(
            model_name='eicrecommendation',
            name='recommendation',
            field=models.SmallIntegerField(choices=[(1, 'Publish'), (-1, 'Ask for minor revision'), (-2, 'Ask for major revision'), (-3, 'Reject')]),
        ),
    ]
