# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-05 10:36
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('gas_dynamics', '0003_auto_20160805_0948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='start_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 5, 10, 36, 0, 626931, tzinfo=utc), verbose_name='date started'),
        ),
    ]