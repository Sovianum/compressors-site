# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-06 12:24
from __future__ import unicode_literals

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BladeProfilePlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('compressor_name', models.CharField(max_length=500)),
                ('plot_image', models.ImageField(upload_to='')),
                ('blade_number', models.IntegerField()),
                ('h_rel', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MeanRadiusSingleCompressorTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('mass_rate', models.FloatField()),
                ('T_stag_1', models.FloatField()),
                ('p_stag_1', models.FloatField()),
                ('min_eta_ad', models.FloatField()),
                ('stage_number', models.IntegerField()),
                ('precision', models.FloatField(default=0.03)),
                ('u_out_1', models.FloatField()),
                ('d_rel_1', models.FloatField()),
                ('H_t_rel_first', models.FloatField()),
                ('H_t_rel_last', models.FloatField()),
                ('H_t_rel_max', models.FloatField()),
                ('H_t_rel_max_coord', models.FloatField()),
                ('eta_ad_first', models.FloatField()),
                ('eta_ad_last', models.FloatField()),
                ('eta_ad_max', models.FloatField()),
                ('eta_ad_max_coord', models.FloatField()),
                ('c_a_rel_first', models.FloatField()),
                ('c_a_rel_last', models.FloatField()),
                ('reactivity_first', models.FloatField()),
                ('reactivity_last', models.FloatField()),
                ('inlet_alpha', models.FloatField()),
                ('constant_diameter_parameters', models.CharField(max_length=200)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('start_date', models.DateTimeField(default=datetime.datetime(2016, 7, 6, 12, 24, 22, 754841, tzinfo=utc), verbose_name='date started')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='meanradiussinglecompressortask',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gas_dynamics.Project'),
        ),
    ]