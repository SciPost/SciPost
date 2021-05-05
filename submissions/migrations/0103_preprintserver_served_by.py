# Generated by Django 2.2.16 on 2021-05-01 17:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0102_auto_20210310_2026'),
    ]

    operations = [
        migrations.AddField(
            model_name='preprintserver',
            name='served_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subsidiaries', to='submissions.PreprintServer'),
        ),
    ]