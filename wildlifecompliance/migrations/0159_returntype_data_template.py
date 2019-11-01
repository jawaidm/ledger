# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-04-26 02:50
from __future__ import unicode_literals

from django.db import migrations, models
import wildlifecompliance.components.returns.models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0158_auto_20190425_1605'),
    ]

    operations = [
        migrations.AddField(
            model_name='returntype',
            name='data_template',
            field=models.FileField(null=True, upload_to=wildlifecompliance.components.returns.models.template_directory_path),
        ),
    ]
