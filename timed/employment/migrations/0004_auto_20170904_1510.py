# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-04 13:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("employment", "0003_user_tour_done")]

    operations = [
        migrations.AlterModelOptions(
            name="absencetype", options={"ordering": ("name",)}
        ),
        migrations.AlterModelOptions(name="location", options={"ordering": ("name",)}),
        migrations.AlterModelOptions(
            name="publicholiday", options={"ordering": ("date",)}
        ),
        migrations.AlterField(
            model_name="absencecredit",
            name="days",
            field=models.IntegerField(default=0),
        ),
    ]
