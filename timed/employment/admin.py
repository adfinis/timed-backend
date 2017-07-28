"""Views for the admin interface."""

import datetime

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from timed.employment import models


class SupervisorInline(admin.TabularInline):
    model = models.User.supervisors.through
    extra = 0
    fk_name = 'from_user'
    verbose_name = _('Supervisor')
    verbose_name_plural = _('Supervisors')


@admin.register(models.User)
class UserAdmin(UserAdmin):
    """Timed specific user admin."""

    inlines = [SupervisorInline]
    exclude = ('supervisors', )


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    """Location admin view."""

    list_display  = ['name']
    search_fields = ['name']


class EmploymentForm(forms.ModelForm):
    """Custom form for the employment admin."""

    def clean(self):
        """Validate the employment as a whole.

        Ensure the end date is after the start date and there is only one
        active employment per user and there are no overlapping employments.

        :throws: django.core.exceptions.ValidationError
        :return: The cleaned data
        :rtype:  dict
        """
        data = super().clean()

        employments = models.Employment.objects.filter(user=data.get('user'))

        if self.instance:
            employments = employments.exclude(id=self.instance.id)

        if (
            data.get('end_date') and
            data.get('start_date') >= data.get('end_date')
        ):
            raise ValidationError(_(
                'The end date must be after the start date'
            ))

        if (
            employments.filter(end_date__isnull=True) and
            data.get('end_date') is None
        ):
            raise ValidationError(_(
                'A user can only have one active employment'
            ))

        if any([
            e.start_date <= (
                data.get('end_date') or
                datetime.date.today()
            ) and data.get('start_date') <= (
                e.end_date or
                datetime.date.today()
            )
            for e
            in employments
        ]):
            raise ValidationError(_(
                'A user can\'t have multiple employments at the same time'
            ))

        return data

    class Meta:
        """Meta information for the employment form."""

        fields = '__all__'
        model = models.Employment


@admin.register(models.Employment)
class EmploymentAdmin(admin.ModelAdmin):
    """Employment admin view."""

    form         = EmploymentForm
    list_display = ['__str__', 'percentage', 'location']
    list_filter  = ['location', 'user']


@admin.register(models.PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    """Public holiday admin view."""

    list_display = ['__str__', 'date', 'location']
    list_filter  = ['location']


@admin.register(models.AbsenceType)
class AbsenceTypeAdmin(admin.ModelAdmin):
    """Absence type admin view."""

    list_display = ['name']


@admin.register(models.AbsenceCredit)
class AbsenceCreditAdmin(admin.ModelAdmin):
    """Absence credit admin view."""

    list_display = ['absence_type', 'user', 'duration', 'date']
    list_filter  = ['absence_type', 'user']


@admin.register(models.OvertimeCredit)
class OvertimeCreditAdmin(admin.ModelAdmin):
    """Overtime credit admin view."""

    list_display = ['user', 'duration', 'date']
    list_filter  = ['user']
