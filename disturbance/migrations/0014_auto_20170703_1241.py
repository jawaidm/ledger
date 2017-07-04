# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-03 04:41
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('disturbance', '0013_referral'),
    ]

    operations = [
        migrations.AddField(
            model_name='referral',
            name='linked',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='referral',
            name='referral_email',
            field=models.EmailField(default='test@dbca.wa.gov.au', max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='referral',
            name='referral_name',
            field=models.CharField(default='test', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='referral',
            name='referral',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='disturbance_referalls', to=settings.AUTH_USER_MODEL),
        ),
    ]
