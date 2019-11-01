# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-10-24 08:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0319_merge_20191022_1545'),
    ]

    operations = [
        migrations.CreateModel(
            name='PenaltyAmount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, default=b'0.00', max_digits=8)),
                ('date_of_enforcement', models.DateField(blank=True, null=True)),
                ('time_of_enforcement', models.DateField(blank=True, null=True)),
                ('section_regulation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='penalty_amounts', to='wildlifecompliance.SectionRegulation')),
            ],
            options={
                'ordering': ('date_of_enforcement', 'time_of_enforcement'),
                'verbose_name': 'CM_PenaltyAmount',
                'verbose_name_plural': 'CM_PenaltyAmounts',
            },
        ),
        migrations.AddField(
            model_name='sanctionoutcome',
            name='penalty_amount',
            field=models.DecimalField(decimal_places=2, default=b'0.00', max_digits=8),
        ),
    ]
