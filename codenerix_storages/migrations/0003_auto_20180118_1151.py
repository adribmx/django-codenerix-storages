# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-01-18 10:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('codenerix_storages', '0002_auto_20180118_1040'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storage',
            name='alias',
        ),
        migrations.AlterField(
            model_name='storagebox',
            name='box_kind',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='storage_boxes', to='codenerix_storages.StorageBoxKind', verbose_name='Box Kind'),
        ),
        migrations.AlterField(
            model_name='storagebox',
            name='box_structure',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='storage_boxes', to='codenerix_storages.StorageBoxStructure', verbose_name='Box Structure'),
        ),
    ]
