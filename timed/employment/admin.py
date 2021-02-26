"""Views for the admin interface."""

import datetime

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from timed.employment import models
from timed.forms import DurationInHoursField

# do not allow deletion of objects site wide
# objects need to be deactivated resp. archived
admin.site.disable_action("delete_selected")


class SupervisorInline(admin.TabularInline):
    model = models.User.supervisors.through
    extra = 0
    fk_name = "from_user"
    verbose_name = _("Supervisor")
    verbose_name_plural = _("Supervisors")


class SuperviseeInline(admin.TabularInline):
    model = models.User.supervisors.through
    extra = 0
    fk_name = "to_user"
    verbose_name = _("Supervisee")
    verbose_name_plural = _("Supervisees")


class EmploymentForm(forms.ModelForm):
    """Custom form for the employment admin."""

    worktime_per_day = DurationInHoursField(label=_("Worktime per day in hours"))

    def clean(self):
        """Validate the employment as a whole.

        Ensure the end date is after the start date and there is only one
        active employment per user and there are no overlapping employments.

        :throws: django.core.exceptions.ValidationError
        :return: The cleaned data
        :rtype:  dict
        """
        data = super().clean()

        employments = models.Employment.objects.filter(user=data.get("user"))

        if self.instance:
            employments = employments.exclude(id=self.instance.id)

        if data.get("end_date") and data.get("start_date") >= data.get("end_date"):
            raise ValidationError(_("The end date must be after the start date"))

        if any(
            [
                e.start_date <= (data.get("end_date") or datetime.date.today())
                and data.get("start_date") <= (e.end_date or datetime.date.today())
                for e in employments
            ]
        ):
            raise ValidationError(
                _("A user can't have multiple employments at the same time")
            )

        return data

    class Meta:
        """Meta information for the employment form."""

        fields = "__all__"
        model = models.Employment


class EmploymentInline(admin.TabularInline):
    form = EmploymentForm
    model = models.Employment
    extra = 0


class OvertimeCreditForm(forms.ModelForm):
    model = models.OvertimeCredit
    duration = DurationInHoursField(label=_("Duration in hours"))


class OvertimeCreditInline(admin.TabularInline):
    model = models.OvertimeCredit
    form = OvertimeCreditForm
    extra = 0


class AbsenceCreditInline(admin.TabularInline):
    model = models.AbsenceCredit
    extra = 0


@admin.register(models.User)
class UserAdmin(UserAdmin):
    """Timed specific user admin."""

    inlines = [
        SupervisorInline,
        SuperviseeInline,
        EmploymentInline,
        OvertimeCreditInline,
        AbsenceCreditInline,
    ]
    list_display = ("username", "first_name", "last_name", "is_staff", "is_active")

    actions = [
        "disable_users",
        "enable_users",
        "disable_staff_status",
        "enable_staff_status",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fieldsets += ((_("Extra fields"), {"fields": ["tour_done"]}),)

    def disable_users(self, request, queryset):
        queryset.update(is_active=False)

    disable_users.short_description = _("Disable selected users")

    def enable_users(self, request, queryset):
        queryset.update(is_active=True)

    enable_users.short_description = _("Enable selected users")

    def disable_staff_status(self, request, queryset):
        queryset.update(is_staff=False)

    disable_staff_status.short_description = _("Disable staff status of selected users")

    def enable_staff_status(self, request, queryset):
        queryset.update(is_staff=True)

    enable_staff_status.short_description = _("Enable staff status of selected users")

    def has_delete_permission(self, request, obj=None):
        return obj and not obj.reports.exists()


@admin.register(models.Location)
class LocationAdmin(admin.ModelAdmin):
    """Location admin view."""

    list_display = ["name"]
    search_fields = ["name"]

    def has_delete_permission(self, request, obj=None):
        return obj and not obj.employments.exists()


@admin.register(models.PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):
    """Public holiday admin view."""

    list_display = ["__str__", "date", "location"]
    list_filter = ["location"]


@admin.register(models.AbsenceType)
class AbsenceTypeAdmin(admin.ModelAdmin):
    """Absence type admin view."""

    list_display = ["name"]

    def has_delete_permission(self, request, obj=None):
        return obj and not obj.absences.exists() and not obj.absencecredit_set.exists()
