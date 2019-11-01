# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-08-08 01:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0273_merge_20190806_1528'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='application_type',
            field=models.CharField(choices=[('new_licence', 'New'), ('new_activity', 'New Activity'), ('amend_activity', 'Amendment'), ('renew_activity', 'Renewal'), ('system_generated', 'System Generated'), ('reissue_activity', 'Reissue')], default='new_licence', max_length=40, verbose_name='Application Type'),
        ),
    ]
