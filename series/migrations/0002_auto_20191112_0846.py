# Generated by Django 2.1.8 on 2019-11-12 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('series', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='series',
            options={'verbose_name_plural': 'series'},
        ),
        migrations.RemoveField(
            model_name='collection',
            name='cover_image',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='logo',
        ),
        migrations.AddField(
            model_name='collection',
            name='image',
            field=models.ImageField(blank=True, upload_to='series/collections/images/'),
        ),
    ]