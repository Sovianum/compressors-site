# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-08 13:07
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('gas_dynamics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 8, 13, 7, 49, 877414, tzinfo=utc), verbose_name='date started'),
        ),
    ]
