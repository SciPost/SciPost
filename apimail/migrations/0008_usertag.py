# Generated by Django 2.1.8 on 2020-01-16 20:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('apimail', '0007_auto_20200116_1955'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=64)),
                ('unicode_symbol', models.CharField(blank=True, max_length=1)),
                ('hex_color_code', models.CharField(max_length=6)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_tags', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
