"""Views for the admin interface."""

from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _
from nested_inline.admin import NestedModelAdmin, NestedStackedInline

from timed.forms import DurationInHoursField
from timed.projects import models
from timed.redmine.admin import RedmineProjectInline
from timed.subscription.admin import CustomerPasswordInline


class CustomerAssigneeInline(admin.TabularInline):
    model = models.CustomerAssignee
    extra = 0


class ProjectAssigneeInline(NestedStackedInline):
    model = models.ProjectAssignee
    extra = 0


class TaskAssigneeInline(NestedStackedInline):
    model = models.TaskAssignee
    extra = 1


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Customer admin view."""

    list_display = ["name"]
    search_fields = ["name"]
    inlines = [CustomerPasswordInline, CustomerAssigneeInline]

    def has_delete_permission(self, request, obj=None):
        return obj and not obj.projects.exists()


@admin.register(models.BillingType)
class BillingType(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(models.CostCenter)
class CostCenter(admin.ModelAdmin):
    list_display = ["name", "reference"]
    search_fields = ["name"]


class TaskForm(forms.ModelForm):
    """
    Task form making sure that initial forms are marked as changed.

    Otherwise when saving project default tasks would not be saved.
    """

    model = models.Task
    estimated_time = DurationInHoursField(
        label=_("Estimated time in hours"), required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs.get("initial")
        if initial:
            self.changed_data = ["name"]


class TaskInlineFormset(BaseInlineFormSet):
    """Task formset defaulting to task templates when project is created."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = kwargs["instance"]
        if project.tasks.count() == 0:
            self.initial = [
                {"name": tmpl.name}
                for tmpl in models.TaskTemplate.objects.order_by("name")
            ]
            self.extra += len(self.initial)


class TaskInline(NestedStackedInline):
    formset = TaskInlineFormset
    form = TaskForm
    model = models.Task
    extra = 0
    inlines = [TaskAssigneeInline]

    def has_delete_permission(self, request, obj=None):
        # for some reason obj is parent object and not task
        # so this doesn't work
        # return obj and not obj.reports.exists()
        return False


class ProjectForm(forms.ModelForm):
    model = models.Project
    estimated_time = DurationInHoursField(
        label=_("Estimated time in hours"), required=False
    )


@admin.register(models.Project)
class ProjectAdmin(NestedModelAdmin):
    """Project admin view."""

    form = ProjectForm
    list_display = ["name", "customer"]
    list_filter = ["customer"]
    search_fields = ["name", "customer__name"]

    inlines = [TaskInline, RedmineProjectInline, ProjectAssigneeInline]

    def has_delete_permission(self, request, obj=None):
        return obj and not obj.tasks.exists()


@admin.register(models.TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    """Task template admin view."""

    list_display = ["name"]
