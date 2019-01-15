# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-17 09:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="BillingType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("website", models.URLField(blank=True)),
                ("comment", models.TextField(blank=True)),
                ("archived", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("comment", models.TextField(blank=True)),
                ("archived", models.BooleanField(default=False)),
                ("estimated_hours", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "billing_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projects",
                        to="projects.BillingType",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="projects",
                        to="projects.Customer",
                    ),
                ),
                (
                    "reviewers",
                    models.ManyToManyField(
                        related_name="reviews", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("estimated_hours", models.PositiveIntegerField(blank=True, null=True)),
                ("archived", models.BooleanField(default=False)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tasks",
                        to="projects.Project",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="TaskTemplate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.AddIndex(
            model_name="customer",
            index=models.Index(
                fields=["name", "archived"], name="projects_cu_name_e0e97a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="task",
            index=models.Index(
                fields=["name", "archived"], name="projects_ta_name_dd9620_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(
                fields=["name", "archived"], name="projects_pr_name_ac60a8_idx"
            ),
        ),
    ]
