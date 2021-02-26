import hashlib

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from timed.forms import DurationInHoursField

from . import models


class PackageForm(forms.ModelForm):
    model = models.Package
    duration = DurationInHoursField(label=_("Duration in hours"), required=True)


@admin.register(models.Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ["billing_type", "duration", "price"]
    form = PackageForm


class CustomerPasswordForm(forms.ModelForm):
    def save(self, commit=True):
        password = self.cleaned_data.get("password")
        if password is not None:
            self.instance.password = hashlib.md5(password.encode()).hexdigest()
        return super().save(commit=commit)


class CustomerPasswordInline(admin.StackedInline):
    form = CustomerPasswordForm
    model = models.CustomerPassword
