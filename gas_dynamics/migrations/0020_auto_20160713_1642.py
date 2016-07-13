# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-13 16:42
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('gas_dynamics', '0019_auto_20160713_1641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 13, 16, 42, 33, 143110, tzinfo=utc), verbose_name='date started'),
        ),
    ]