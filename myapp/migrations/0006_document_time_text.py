# Generated by Django 2.1.7 on 2019-07-16 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0005_auto_20190716_0001'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='time_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]