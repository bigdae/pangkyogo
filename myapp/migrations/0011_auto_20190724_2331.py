# Generated by Django 2.2.3 on 2019-07-24 23:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_auto_20190724_2322'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentconvert',
            name='place',
        ),
        migrations.RemoveField(
            model_name='documentconvert',
            name='place_convert',
        ),
    ]