# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-02 07:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attend_server', '0004_auto_20160727_2028'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendance',
            name='time',
            field=models.BigIntegerField(unique=True),
        ),
    ]