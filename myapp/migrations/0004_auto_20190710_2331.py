# Generated by Django 2.1.7 on 2019-07-10 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0003_auto_20190710_2247'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='dup',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='document',
            name='time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]