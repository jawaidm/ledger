# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-19 06:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import taggit.managers
import datetime

class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('parkstay', '0003_auto_20161013_1138'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=12)),
            ],
        ),
        migrations.RenameModel(
            old_name='CampgroundFeature',
            new_name='Feature',
        ),
        migrations.RenameField(
            model_name='campground',
            old_name='rules',
            new_name='regulations',
        ),
        migrations.RemoveField(
            model_name='campground',
            name='fees',
        ),
        migrations.RemoveField(
            model_name='campground',
            name='is_published',
        ),
        migrations.RemoveField(
            model_name='campground',
            name='key',
        ),
        migrations.RemoveField(
            model_name='campground',
            name='metakeywords',
        ),
        migrations.RemoveField(
            model_name='campground',
            name='othertransport',
        ),
        migrations.AddField(
            model_name='campground',
            name='check_in',
            field=models.TimeField(default=datetime.time(14)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campground',
            name='check_out',
            field=models.TimeField(default=datetime.time(10)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campground',
            name='dog_permitted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='campground',
            name='max_dba',
            field=models.SmallIntegerField(default=180),
        ),
        migrations.AddField(
            model_name='campground',
            name='min_dba',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='campground',
            name='no_booking_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='campground',
            name='no_booking_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='campground',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
        migrations.AddField(
            model_name='campsite',
            name='features',
            field=models.ManyToManyField(to='parkstay.Feature'),
        ),
        migrations.AddField(
            model_name='campsiteclass',
            name='dimensions',
            field=models.CharField(default='6x4', max_length=12),
        ),
        migrations.AddField(
            model_name='campsiteclass',
            name='hard_surface',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='campground',
            name='campground_type',
            field=models.SmallIntegerField(choices=[(0, 'Campground: no bookings'), (1, 'Campground: book online'), (2, 'Campground: book by phone'), (3, 'Other accomodation'), (4, 'Not Published')], default=0),
        ),
        migrations.AddField(
            model_name='campground',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='parkstay.Contact'),
        ),
    ]
