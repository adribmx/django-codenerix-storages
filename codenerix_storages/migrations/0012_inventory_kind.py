# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-02-15 16:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('codenerix_storages', '0011_merge_20180202_0726'),
    ]

    operations = [
        migrations.AddField(
            model_name='inventory',
            name='kind',
            field=models.CharField(choices=[('B', 'Internal'), ('I', 'Input'), ('O', 'Output')], default='B', editable=False, max_length=1, verbose_name='Kind'),
        ),
    ]
