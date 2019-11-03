# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-10-16 07:01
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0314_auto_20191016_1436'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalCasePriority',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('case_priority', models.CharField(max_length=50)),
                ('schema', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
                ('version', models.SmallIntegerField(default=1)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('replaced_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='wildlifecompliance.LegalCasePriority')),
            ],
            options={
                'verbose_name': 'CM_CasePriority',
                'verbose_name_plural': 'CM_CasePriorities',
            },
        ),
        migrations.AlterUniqueTogether(
            name='legalcasepriority',
            unique_together=set([('case_priority', 'version')]),
        ),
    ]
