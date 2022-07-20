"""Models for the projects app."""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from djmoney.models.fields import MoneyField

from timed.tracking.models import Report


class Customer(models.Model):
    """Customer model.

    A customer is a person or company which will pay the work
    reported on their projects.
    """

    name = models.CharField(max_length=255, unique=True)
    reference = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    comment = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="CustomerAssignee",
        related_name="assigned_to_customers",
    )

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return self.name

    class Meta:
        """Meta informations for the customer model."""

        ordering = ["name"]


class CostCenter(models.Model):
    """Cost center defining how cost of projects and tasks are allocated."""

    name = models.CharField(max_length=255, unique=True)
    reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class BillingType(models.Model):
    """Billing type defining how a project, resp. reports are being billed."""

    name = models.CharField(max_length=255, unique=True)
    reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Project(models.Model):
    """Project model.

    A project is an offer in most cases. It has multiple tasks and
    belongs to a customer.
    """

    name = models.CharField(max_length=255, db_index=True)
    reference = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    comment = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    billed = models.BooleanField(default=False)
    estimated_time = models.DurationField(blank=True, null=True)
    customer = models.ForeignKey(
        "projects.Customer", on_delete=models.CASCADE, related_name="projects"
    )
    billing_type = models.ForeignKey(
        BillingType,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="projects",
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="projects",
    )
    customer_visible = models.BooleanField(default=False)
    amount_offered = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    amount_invoiced = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectAssignee",
        related_name="assigned_to_projects",
    )
    remaining_effort_tracking = models.BooleanField(default=False)
    total_remaining_effort = models.DurationField(default=timedelta(0))

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return "{0} > {1}".format(self.customer, self.name)

    class Meta:
        ordering = ["name"]


class Task(models.Model):
    """Task model.

    A task is a certain activity type on a project. Users can
    report their activities and reports on it.
    """

    name = models.CharField(max_length=255)
    reference = models.CharField(max_length=255, db_index=True, blank=True, null=True)
    estimated_time = models.DurationField(blank=True, null=True)
    archived = models.BooleanField(default=False)
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="tasks"
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="tasks",
    )
    amount_offered = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    amount_invoiced = MoneyField(
        max_digits=10, decimal_places=2, default_currency="CHF", blank=True, null=True
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TaskAssignee",
        related_name="assigned_to_tasks",
    )
    most_recent_remaining_effort = models.DurationField(blank=True, null=True)

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return "{0} > {1}".format(self.project, self.name)

    class Meta:
        """Meta informations for the task model."""

        ordering = ["name"]


class TaskTemplate(models.Model):
    """Task template model.

    A task template is a global template of a task which should
    be generated for every project.
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        """Represent the model as a string.

        :return: The string representation
        :rtype:  str
        """
        return self.name

    class Meta:
        ordering = ["name"]


class CustomerAssignee(models.Model):
    """Customer assignee model.

    Customer assignee is an employee that is assigned to a specific customer.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_assignees",
    )
    customer = models.ForeignKey(
        "projects.Customer", on_delete=models.CASCADE, related_name="customer_assignees"
    )
    is_resource = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)


class ProjectAssignee(models.Model):
    """Project assignee model.

    Project assignee is an employee that is assigned to a specific project.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_assignees",
    )
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="project_assignees"
    )
    is_resource = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)


class TaskAssignee(models.Model):
    """Task assignee model.

    Task assignee is an employee that is assigned to a specific task.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_assignees",
    )
    task = models.ForeignKey(
        "projects.Task", on_delete=models.CASCADE, related_name="task_assignees"
    )
    is_resource = models.BooleanField(default=False)
    is_reviewer = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=False)


@receiver(pre_save, sender=Project)
def update_billed_flag_on_reports(sender, instance, **kwargs):
    """Update billed flag on all reports from the updated project.

    Only update reports if the billed flag on the project was changed.
    Setting the billed flag to True on a project in Django Admin should set
    all existing reports to billed=True. Same goes for setting the flag to billed=False.
    The billed flag should primarily be set in frontend.
    This is only a quicker way for the accountants to update all reports at once.
    """
    # check whether the project was created or is being updated
    if instance.pk:
        if instance.billed != Project.objects.get(id=instance.id).billed:
            Report.objects.filter(Q(task__project=instance)).update(
                billed=instance.billed
            )
