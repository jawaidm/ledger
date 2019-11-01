# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-04-04 02:04
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0036_wildlifelicenceactivity_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wildlifelicenceactivity',
            name='schema',
            field=django.contrib.postgres.fields.jsonb.JSONField(
                default={
                    'defalut': 'default'}),
        ),
    ]
