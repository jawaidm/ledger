# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-31 05:07
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bpay', '0011_auto_20170329_1131'),
    ]

    state_operations = [
        migrations.RemoveField(
            model_name='billercoderecipient',
            name='app',
        ),
        migrations.RemoveField(
            model_name='bpayaccountrecord',
            name='file',
        ),
        migrations.RemoveField(
            model_name='bpayaccounttrailer',
            name='file',
        ),
        migrations.DeleteModel(
            name='BpayFile',
        ),
        migrations.RemoveField(
            model_name='bpayfiletrailer',
            name='file',
        ),
        migrations.RemoveField(
            model_name='bpaygrouprecord',
            name='file',
        ),
        migrations.RemoveField(
            model_name='bpaygrouptrailer',
            name='file',
        ),
        migrations.AlterUniqueTogether(
            name='bpaytransaction',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='bpaytransaction',
            name='file',
        ),
        migrations.DeleteModel(
            name='BillerCodeRecipient',
        ),
        migrations.DeleteModel(
            name='BillerCodeSystem',
        ),
        migrations.DeleteModel(
            name='BpayAccountRecord',
        ),
        migrations.DeleteModel(
            name='BpayAccountTrailer',
        ),
        migrations.DeleteModel(
            name='BpayFileTrailer',
        ),
        migrations.DeleteModel(
            name='BpayGroupRecord',
        ),
        migrations.DeleteModel(
            name='BpayGroupTrailer',
        ),
        migrations.DeleteModel(
            name='BpayTransaction',
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
        ),
    ] 
