# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-25 19:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('linked_domain', '0007_auto_20180215_1434'),
    ]

    operations = [
        migrations.AddField(
            model_name='domainlinkhistory',
            name='hidden',
            field=models.BooleanField(default=False),
        )
    ]
