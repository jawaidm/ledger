# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-22 23:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0091_auto_20181023_0711'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationcondition',
            name='return_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.ReturnType'),
        ),
        migrations.AddField(
            model_name='applicationstandardcondition',
            name='return_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.ReturnType'),
        ),
        migrations.AddField(
            model_name='defaultcondition',
            name='return_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.ReturnType'),
        ),
    ]
