# Generated by Django 2.2.16 on 2020-09-25 14:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0020_auto_20200925_1617'),
    ]

    operations = [
        migrations.AddField(
            model_name='potentialfellowship',
            name='college',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='potential_fellowships', to='colleges.College'),
        ),
    ]