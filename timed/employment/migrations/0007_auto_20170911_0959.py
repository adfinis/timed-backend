# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-11 07:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("employment", "0006_auto_20170906_1635")]

    operations = [
        migrations.AlterField(
            model_name="absencecredit",
            name="absence_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="employment.AbsenceType"
            ),
        )
    ]
