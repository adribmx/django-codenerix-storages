# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-23 18:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codenerix_storages', '0016_auto_20180223_1846'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventoryoutline',
            name='caducity',
            field=models.DateField(blank=True, default=None, null=True, verbose_name='Caducity'),
        ),
    ]
