# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-29 13:20
from __future__ import unicode_literals
from django.db.models import Count

from django.db import migrations, models


def migrate_projects(apps, schema_editor):
    """Set subsctition_project on Projects with orders."""
    Project = apps.get_model("projects", "Project")
    visible_projects = Project.objects.annotate(count_orders=Count("orders")).filter(
        archived=False, count_orders__gt=0
    )
    visible_projects.update(customer_visible=True)


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0006_auto_20171010_1423"),
        ("subscription", "0003_auto_20170907_1151"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="customer_visible",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migrate_projects),
    ]
