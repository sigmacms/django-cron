# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='last_run',
            field=models.DateTimeField(default=None, null=True),
        ),
    ]
