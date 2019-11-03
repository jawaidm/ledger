# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2019-10-21 06:31
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wildlifecompliance', '0314_auto_20191017_1410'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfringementPenalty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('send_invoice', models.BooleanField(default=False)),
                ('confirmation_sent', models.BooleanField(default=False)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('expiry_time', models.DateTimeField(blank=True, null=True)),
                ('payment_type', models.SmallIntegerField(choices=[(0, 'Internet booking'), (1, 'Reception booking'), (2, 'Black booking'), (3, 'Temporary reservation')], default=0)),
                ('cost', models.DecimalField(decimal_places=2, default='0.00', max_digits=8)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='created_by_infringement_penalty', to=settings.AUTH_USER_MODEL)),
                ('sanction_outcome', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='infringement_penalties', to='wildlifecompliance.SanctionOutcome')),
            ],
        ),
        migrations.CreateModel(
            name='InfringementPenaltyInvoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_reference', models.CharField(blank=True, default='', max_length=50, null=True)),
                ('infringement_penalty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='infringement_penalty_invoices', to='wildlifecompliance.InfringementPenalty')),
            ],
        ),
    ]
