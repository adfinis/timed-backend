from django.contrib import admin

from . import models


@admin.register(models.Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['billing_type', 'duration', 'price']
