# Generated by Django 2.2.9 on 2020-07-29 14:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auto_20200729_1649'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Comment',
        ),
    ]
