# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from __future__ import absolute_import
from django.db import migrations

from corehq.sql_db.operations import noop_migration


class Migration(migrations.Migration):

    dependencies = [
        ('form_processor', '0039_auto_20151130_1748'),
    ]

    operations = [
        noop_migration()
    ]
