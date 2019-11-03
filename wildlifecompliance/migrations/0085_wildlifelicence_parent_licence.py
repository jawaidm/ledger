# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-09-26 04:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0084_auto_20180924_1524'),
    ]

    operations = [
        migrations.AddField(
            model_name='wildlifelicence',
            name='parent_licence',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children_licence', to='wildlifecompliance.WildlifeLicence'),
        ),
    ]
