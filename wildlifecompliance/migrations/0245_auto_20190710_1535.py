# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-07-10 07:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0244_auto_20190710_1504'),
    ]

    operations = [
        migrations.AddField(
            model_name='callemaillogdocument',
            name='input_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='callemaillogdocument',
            name='version_comment',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
