# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-08-01 07:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0067_auto_20180801_1228'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessment',
            name='licence_activity_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.WildlifeLicenceActivityType'),
        ),
    ]
