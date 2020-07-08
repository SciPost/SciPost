# Generated by Django 2.1.8 on 2020-01-18 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apimail', '0010_auto_20200118_0806'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usertag',
            name='variant',
            field=models.CharField(choices=[('primary', 'primary'), ('secondary', 'secondary'), ('success', 'success'), ('warning', 'warning'), ('danger', 'danger'), ('info', 'info'), ('light', 'light'), ('dark', 'dark')], default='info', max_length=16),
        ),
    ]